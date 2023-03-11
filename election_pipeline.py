"""
A module for integrating datasets on U.S. 2022 Midterm Election: results,
predictions, election_denialism into a sqlite database.

"""

# Author: Jonathan Collier


import pandas as pd
import numpy as np
import sqlite3 as sql
from dataclasses import dataclass, field
from contextlib import closing


class ElectionQuery:
    """
    A class to store Election queries.
    
    Parameters
    ----------
    None
    
    Attributes
    ----------
    steps : dict 
        A nested dictionary containing queries for building
        a sqlite database of Midterm Election data.
        
    """
    steps = {
        'create_tables': {
            """
            CREATE TABLE IF NOT EXISTS races
                (
                race_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL, 
                state_code TEXT NOT NULL,
                cycle INT NOT NULL,
                office TEXT NOT NULL,
                district TEXT NOT NULL,
                CONSTRAINT race_unique UNIQUE (state_code, district, office)
                );
            """,
            """
            CREATE TABLE IF NOT EXISTS predictions
                (
                prediction_id INTEGER PRIMARY KEY,
                candidate TEXT NOT NULL,
                chance_of_winning NUMERIC,
                average_voteshare NUMERIC,
                forecast_date TEXT NULL,
                CONSTRAINT prediction_unique UNIQUE (candidate, forecast_date)
                );
            """,
            """
            CREATE TABLE IF NOT EXISTS results
                (
                result_id INTEGER PRIMARY KEY,
                first_name TEXT NULL,
                last_name TEXT NOT NULL,
                total_votes INT NOT NULL,
                percent_total_vote NUMERIC NOT NULL,
                political_party TEXT NULL,
                is_incumbent BOOLEAN,
                is_winner BOOLEAN
                );
            """,
            """
            CREATE TABLE IF NOT EXISTS election_mappings
                (
                election_mapping_id INTEGER PRIMARY KEY,
                result_id INT NOT NULL,
                prediction_id INT NOT NULL,
                race_id INT NOT NULL, 
                FOREIGN KEY (result_id) REFERENCES results(result_id),
                FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id),
                FOREIGN KEY (race_id) REFERENCES races(race_id)
                );
            """,
            """
            CREATE TABLE IF NOT EXISTS stances
                (
                stance_id INTEGER PRIMARY KEY,
                election_mapping_id INT NOT NULL,
                stance TEXT NOT NULL,
                source TEXT NULL,
                url TEXT NULL,
                FOREIGN KEY (election_mapping_id) REFERENCES election_mappings(election_mapping_id)
                );
            """
        },
        'create_staging_table': {
            """
            CREATE TABLE elections_stage
            AS
            SELECT 
                ned.state,
                ned.state_code,
                '2022' AS cycle,
                ned.office,
                ned.district,
                ned.first_name,
                CASE 
                WHEN ned.last_name IN ('Write-ins', 'None of these candidates')
                THEN ned.last_name || '-' || ned.state_code || '-' || ned.district
                ELSE ned.last_name END AS last_name,
                ned.total_votes,
                ned.percent_total_vote,
                ned.political_party,
                ned.is_incumbent,
                ned.is_winner,
                CASE 
                WHEN nm.combined_toplines_candidate = 'all others' 
                THEN nm.combined_toplines_candidate || '-' || ned.state_code || '-' || ned.district
                ELSE ct.candidate END AS candidate, 
                ct.chance_of_winning,
                ct.average_voteshare,
                ct.forecast_date,
                ed.stance,
                ed.source,
                ed.url
            FROM name_mappings nm
            LEFT JOIN combined_toplines ct
            ON nm.combined_toplines_candidate = ct.candidate
            AND nm.state_code = ct.state_code
            AND nm.district = ct.district
            JOIN nbc_election_data ned
            ON IFNULL(ned.first_name, '') = IFNULL(nm.nbc_first_name, '')
            AND ned.last_name = nm.nbc_last_name
            AND ned.district = nm.district
            AND ned.state_code = nm.state_code
            LEFT JOIN election_deniers ed
            ON election_deniers_candidate = ed.candidate;
            """
        },
        'load_tables': {
            """
            INSERT INTO races
                (
                state, 
                state_code,
                cycle,
                office,
                district
                )
            SELECT DISTINCT
                es.state,
                es.state_code,
                es.cycle,
                es.office,
                es.district
            FROM elections_stage es
            LEFT JOIN races r
            ON es.state_code = r.state_code
            AND es.district = r.district
            WHERE r.state_code IS NULL
            AND r.district IS NULL;

            INSERT INTO predictions
                (
                candidate,
                chance_of_winning,
                average_voteshare,
                forecast_date
                )
            SELECT DISTINCT
                es.candidate,
                IFNULL(es.chance_of_winning, 0),
                IFNULL(es.average_voteshare, 0),
                es.forecast_date
            FROM elections_stage es
            LEFT JOIN predictions p 
            ON es.candidate = p.candidate
            WHERE p.candidate IS NULL;

            INSERT INTO results
                (
                first_name,
                last_name,
                total_votes,
                percent_total_vote,
                political_party,
                is_incumbent,
                is_winner
                )
            SELECT 
                es.first_name,
                es.last_name,
                es.total_votes,
                es.percent_total_vote,
                es.political_party,
                es.is_incumbent,
                es.is_winner
            FROM elections_stage es
            LEFT JOIN results rs
            ON IFNULL(es.first_name, '') = IFNULL(rs.first_name, '')
            AND es.last_name = rs.last_name
            WHERE rs.first_name IS NULL
            AND rs.last_name IS NULL;

            INSERT INTO election_mappings
                (
                prediction_id,
                result_id,
                race_id
                )
            SELECT DISTINCT
                p.prediction_id,
                rs.result_id,
                r.race_id
            FROM elections_stage es
            JOIN predictions p 
            ON es.candidate = p.candidate
            JOIN races r
            ON r.state_code = es.state_code
            AND r.district = es.district
            JOIN results rs
            ON IFNULL(rs.first_name, '') = IFNULL(es.first_name, '')
            AND rs.last_name = es.last_name
            LEFT JOIN election_mappings em
            ON p.prediction_id = em.prediction_id
            AND r.race_id = em.race_id
            AND rs.result_id = em.result_id
            WHERE em.prediction_id IS NULL
            AND em.result_id IS NULL
            AND em.race_id IS NULL;
            
            INSERT INTO stances 
                (
                election_mapping_id,
                stance,
                source,
                url
                )
            SELECT 
                em.election_mapping_id,
                es.stance,
                es.source,
                es.url
            FROM elections_stage es 
            JOIN predictions p 
            ON es.candidate = p.candidate
            JOIN results rs
            ON IFNULL(rs.first_name, '') = IFNULL(es.first_name, '')
            AND rs.last_name = es.last_name
            JOIN races r
            ON r.state_code = es.state_code
            AND r.district = es.district
            JOIN election_mappings em
            ON em.race_id = r.race_id
            AND em.result_id = rs.result_id
            AND em.prediction_id = p.prediction_id
            LEFT JOIN stances s
            ON s.election_mapping_id = em.election_mapping_id
            WHERE es.stance IS NOT NULL
            AND s.election_mapping_id IS NULL;
            """
        },
        'update_tables': {
            """
            ALTER TABLE races
            ADD race_forecast TEXT NULL;


            CREATE TEMPORARY TABLE race_forecasts
            (
                race_id INTEGER NOT NULL,
                race_forecast TEXT NOT NULL
            );


            INSERT INTO temp.race_forecasts (
                race_id,
                race_forecast
            )
            SELECT 
                race_id,
                CASE 
                WHEN SUM(rep_chance_of_winning) >= .95 THEN 'Solid-R'
                WHEN SUM(rep_chance_of_winning) >= .75 THEN 'Likely-R'
                WHEN SUM(rep_chance_of_winning) >= .60 THEN 'Lean-R'
                WHEN SUM(dem_chance_of_winning) >= .95 THEN 'Solid-D'
                WHEN SUM(dem_chance_of_winning) >= .75 THEN 'Likely-D'
                WHEN SUM(dem_chance_of_winning) >= .60 THEN 'Lean-D'
                ELSE 'Toss-Up' END AS race_call
            FROM 
                (
                SELECT 
                    r.race_id, 
                    CASE 
                    WHEN political_party = 'Dem' THEN chance_of_winning
                    ELSE 0 END AS dem_chance_of_winning,
                    CASE 
                    WHEN political_party = 'Rep' THEN chance_of_winning
                    ELSE 0 END AS rep_chance_of_winning
                FROM predictions p
                JOIN election_mappings em
                ON em.prediction_id = p.prediction_id
                JOIN results rs
                ON rs.result_id = em.result_id
                JOIN races r
                ON r.race_id = em.race_id
                ) sub
            GROUP BY race_id;


            UPDATE races
            SET race_forecast = (
                                SELECT race_forecast
                                FROM temp.race_forecasts rf
                                WHERE rf.race_id = races.race_id
                                );
            """ 
        },
        'drop_staging_table': {
            """DROP TABLE elections_stage"""
        }
    }


@dataclass
class NbcElectionData:
    """
    A dataclass that stores and preprocesses
    nbc_election_data DataFrame.
    
    Parameters
    ----------
    path : str, default='data/nbc_election_data.csv'
        The path used to import data.
    
    Attributes
    ----------
    data : pandas.DataFrame
        A DataFrame of nbc_election_data.
    """
    data: pd.DataFrame = field(init=False)
    path: str = 'data/nbc_election_data.csv'
    
    def __post_init__(self):
        self.data = (pd.read_csv(self.path)
                     .pipe(self.parse_state_code)
                     .pipe(self.parse_office)
                     .pipe(self.parse_district)
                     .pipe(pd.DataFrame.drop, 
                           columns=['state_code', 'Unnamed: 0'])
                     .pipe(pd.DataFrame.rename, 
                           columns={'parsed_state_code': 'state_code'}))
    
    @staticmethod
    def parse_state_code(data):
        """
        Parses state_code values from `state_code` column
        in a copy of input parameter `data`, and returns the resulting
        DataFrame.
        
        Parameters
        ----------
        data : pandas.DataFrame
            A DataFrame of nbc_election_data.
        Returns
        -------
        data : pandas.DataFrame
            A copy of `data` with state_code parsed from `state_code` column
            with the result assigned to column `parsed_state_code`.
        """
        data = data.copy()
        data['parsed_state_code'] = data['state_code'].str.slice(0,2)
        return data
    
    @staticmethod
    def parse_office(data):
        """
        Parses office from `state_code` column in a copy of input parameter 
        `data`, and returns the resulting DataFrame.
        
        Parameters
        ----------
        data : pandas.DataFrame
            A DataFrame of nbc_election_data.
        Returns
        -------
        data : pandas.DataFrame
            A copy of input parameter `data` with `state_code` column parsed 
            for ('House', 'Senate') with result assigned to column `office`.
        """
        data = data.copy()
        data['office'] = ['House' if 'House' in state_code else 'Senate' 
                          for state_code in data['state_code']]
        return data
    
    @staticmethod
    def parse_district(data):
        """
        Returns a copy of input parameter `data` with `state_code` column
        parsed for House candidates for district values (i.e., 1, 2, etc.) 
        assigns the result to a new column `district`. Defaults `district`
        to 'S3' for Senate candidates, except where 
        `race_name`='Oklahoma Seat 2'.
        
        Parameters
        ----------
        data : pandas.DataFrame
            A DataFrame of nbc_election_data data.
        
        Returns
        -------
        data : pandas.DataFrame
            A copy of input parameter `data` with new column `district`,
            which is assigned default values for Senate candidates,
            and for House candidates values are parsed from `state_code`
            column. 
        """
        data = data.copy()
        data['district'] = np.where(data['office'] == 'House', 
                                    data['state_code'].str.extract('(\d+)', 
                                    expand=False), 'S3')
        data.loc[(data['race_name'] == 'Oklahoma Seat 2'), 'district'] = 'S2'
        
        return data
        
        
@dataclass 
class ElectionDeniers:
    """
    A dataclass that stores and preprocesses election_deniers DataFrame.
    
    Parameters
    ----------
    path : str
        The path used to import data.
    
    Attributes
    ----------
    data : pandas.DataFrame
        A DataFrame of election_deniers data.
    """
    data: pd.DataFrame = field(init=False)
    path: str = 'data/election_deniers.csv'
    
    def __post_init__(self):
        self.data = (pd.read_csv(self.path)
                    .pipe(self.set_columns_to_lowercase)
                    .pipe(self.filter_offices))
        
    @staticmethod
    def set_columns_to_lowercase(data):
        """
        Returns a copy of input parameter `data` with column names set to 
        lowercase.
        
        Parameters
        ----------
        data : pandas.DataFrame
            A DataFrame of election_deniers data.
        
        Returns
        -------
        data : pandas.DataFrame
            A copy of input parameter `data` with column names set to 
            lowercase.
        """
        data = data.copy()
        data.columns = [column.lower() for column in data.columns]
        return data
        
    @staticmethod
    def filter_offices(data):
        """
        Filters a copy of input parameter `data` by `office` column on 
        specific values in `office`: 'Senator', 'Representative', 
        'Senator (unexpired term)' and returns the resulting DataFrame.
        
        Parameters
        ----------
        data : pandas.DataFrame
            A DataFrame of election_deniers data.
        
        Returns
        -------
        : pandas.DataFrame
            A copy of input parameter `data` filtered by values in the 
            `office` column. 
        """
        data = data.copy()
        selected_offices = ['Senator', 
                            'Representative', 
                            'Senator (unexpired term)']
        return data[data['office'].isin(selected_offices)]

    
@dataclass 
class CombinedToplines:
    """
    A dataclass that stores and preprocesses combined_toplines 
    DataFrame (i.e., Senate and House candidate prediction data from
    FiveThirtyEight).
    
    
    Parameters
    ----------
    path : str
        The path used to import data.
    
    Attributes
    ----------
    data : pandas.DataFrame
        A DataFrame of combined_toplines data.  
    """
    data: pd.DataFrame = field(init=False)
    senate_path: str = 'data/senate_state_toplines_2022.csv'
    house_path: str = 'data/house_district_toplines_2022.csv'
    
    def __post_init__(self):
        self.data = (pd.concat([pd.read_csv(self.house_path, 
                                           low_memory=False), 
                               pd.read_csv(self.senate_path)],
                               axis=0).reset_index()
                    .pipe(self.union_combined_toplines)
                    .pipe(self.parse_district)
                    .pipe(self.parse_state_code)
                    .pipe(pd.DataFrame.drop, columns=['district'])
                    .pipe(pd.DataFrame.rename, 
                          columns={'parsed_district': 'district',
                                   'parsed_state_code' : 'state_code'}))
    
    @staticmethod
    def parse_district(data):
        """
        Parses district values from `district` column in a copy of input 
        parameter `data`, assigns the result to column `parsed_district`,
        and returns the resulting DataFrame.
        
        Parameters
        ----------
        data : pandas.DataFrame
            A DataFrame of combined_toplines data.
        
        Returns
        -------
        data : pandas.DataFrame
            DataFrame with district values (1, 2, etc.) parsed 
            and assigned to column `parsed_district`.
            
        """
        
        data = data.copy()
        data['parsed_district'] = (data['district']
                                   .apply(lambda district: 
                                          district[3:len(district)]))
        return data
    
    @staticmethod
    def parse_state_code(data):
        """
        Parses state_code values from `district` column in a copy of 
        input parameter `data`, assigns the result to column 
        `parsed_state_code`, and returns the resulting DataFrame.
        
        Parameters
        ----------
        data : pandas.DataFrame
            A DataFrame of combined_toplines data.
        
        Returns
        -------
        data : pandas.DataFrame
            A copy of input parameter `data` with state_code values parsed 
            from `district` column, and assigned to new column: 
            `parsed_state_code`.
        """
        
        data = data.copy()
        data['parsed_state_code'] = data['district'].str.slice(0,2)

        return data
    
    @staticmethod
    def union_combined_toplines(data):
        """
        Returns unioned subsets of DataFrames: 'senate_state_toplines_2022' and 
        'house_district_toplines_2022' as a single DataFrame.
        
        Parameters
        ----------
        data : pandas.DataFrame
            A DataFrame of Senate_Stage and House_District Toplines.
        
        Returns 
        -------
        : pandas.DataFrame
            A flattened DataFrame of Senate_Stage and House_District Toplines.
        
        """
        
        data = data.copy()
        
        name, winner, voteshare  = 'name_{}', 'winner_{}', 'voteshare_mean_{}'
        party_seat_names = ['D1','D2','D3','D4','R1',
                            'R2','R3','R4','I1','O1']         
        flattened_data = []
        for index, party_seat_name in enumerate(party_seat_names):
            flattened_data.append(
                data[['cycle', 
                      'forecastdate', 
                      'branch', 
                      'district',
                      name.format(party_seat_name), 
                      winner.format(party_seat_name),
                      voteshare.format(party_seat_name)]]
                     [(data[name.format(party_seat_name)].notnull())
                      & (pd.to_datetime(data['forecastdate']) == '2022-11-08')  
                      & (data['expression'] == '_deluxe')].values)
                                      
                                      
                                      
        return pd.DataFrame(data=np.concatenate(flattened_data), 
                            columns=['cycle', 
                                     'forecast_date', 
                                     'branch', 
                                     'district', 
                                     'candidate', 
                                     'chance_of_winning', 
                                     'average_voteshare'])
                                     
                                     
@dataclass
class NameMappings:
    """
    A dataclass that stores name_mappings DataFrame.
    """
    data: pd.DataFrame = field(init=False)
    path: str = 'data/name_mappings.csv'
    
    def __post_init__(self):
        self.data = (pd.read_csv(self.path)
                    .drop(columns=['Unnamed: 0']))

       
class ElectionPipeline:
    """
    A class for integrating election datasets into a sqlite database.
    
    Parameters
    ----------
    database, default='data\elections.db'
        The path of the database.

    Attributes
    ----------
    database 
        Stores the path of the database.
    queries:
        Stores sql queries for the pipeline to build and add data to the 
        database.
    source_data:
        Stores the source data files for adding data to the database.
    """
    def __init__(self, database='data\elections.db'):
        self.database = database
        self.queries = ElectionQuery()
        self.source_data = {'nbc_election_data': NbcElectionData().data,
                            'name_mappings': NameMappings().data,
                            'combined_toplines': CombinedToplines().data,
                            'election_deniers': ElectionDeniers().data}
    
    def create_database(self):
        """
        Creates a database from `source_data` files using `database`.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        
        """
        try:
            with sql.connect(self.database) as conn:
                for table_name, data in self.source_data.items():
                    data.to_sql(table_name, 
                                con=conn, 
                                if_exists='replace', 
                                index=False)          
        except Exception as e:
            print(e)

    def run_step(self, key):
        """
        Runs a step in `queries.steps`, if `key` exists.
        
        Parameters
        ----------
        key : 
            A key in `queries.steps`.
        
        Returns
        -------
        None
        
        """
        if key in self.queries.steps:
            try:
                with sql.connect(self.database) as conn:
                    for query in self.queries.steps[key]:
                        with closing(conn.cursor()) as cursor:
                            cursor.executescript(query)
                            conn.commit()
            except Exception as e:
                print(e)
        else:
            raise Exception('{key} does not exist in steps'.format(key))  
            
    def run_query(self, query: str):
        """
        Reads SQL `query` result into a pandas DataFrame using 
        database connection.
        
        Parameters
        ----------
        query : str
            Sql query string to be executed.
        
        Returns
        -------
        : pandas.DataFrame
            The sql query result.
        """
        try:
            with sql.connect(self.database) as conn:
                return pd.read_sql(query, con=conn)
        
        except Exception as e:
            print(e)
    
        
        

        
    
    

    
        
        
    
    
        
    
        
    
    
    

    
