# Project-1

## Libraries used in this project:
<ol>
  <li> pandas</li>
  <li> matplotlib </li>
  <li> seaborn</li>
  <li> numpy </li>
  <li> dataclasses</li>
  <li> sqlite3 </li>
  <li> typing </li>
  <li> contextlib </li>
  <li> bs4 </li>
  <li> requests </li>
</ol>

## Motivation for the project:
This project was inspired by an article by <a href="https://projects.fivethirtyeight.com/republicans-trump-election-fraud/">FiveThirtyEight</a> which looked at stances on the 2020 U.S. Presidential Election results amongst GOP candidates (Senate, House, Secretary of State, etc.) that were running in the 2022 U.S. Midterms. I specifically wanted to look at Congressional candidates and do a follow-up to see how the candidates that Fully Denied the election ended up performing in 2022 Midterms. I also wanted to add another layer which was looking at incumbent candidates - I was interested in how this played a role in how candidates were projected to perform and how they ultimately performed in the Midterms. 

## Files in this repository:
<ol>
  <li>data/
    <ol>
        <li><b>election_deniers.csv</b>: This file is from FiveThirtyEight's <a href="https://github.com/fivethirtyeight/data/tree/master/election-deniers">Election Deniers</a> dataset - it contains "views of every Republican candidate for Senate, House, governor, attorney general and secretary of state running in the 2022 general election on the legitimacy of the 2020 election."</li>
        <li><b>house_district_toplines.csv</b>: This file is from FiveThirtyEight's <a href="https://github.com/fivethirtyeight/data/tree/master/election-forecasts-2022">Election Forecasts 2022</a> dataset - it includes predictions for candidates running for the House of Representatives in the 2022 Midterm elections.</li>
        <li><b>senate_state_toplines.csv</b>: This file is from FiveThirtyEight's <a href="https://github.com/fivethirtyeight/data/tree/master/election-forecasts-2022">Election Forecasts 2022</a> dataset - it includes predictions for candidates running for the Senate in the 2022 Midterm elections.</li>
        <li><b>nbc_election_data.csv</b>: This file includes Midterm election results that I scraped from NBC using python libraries: requests and bs4 BeautifulSoup. I         also supplemented this file with some manual entry to ensure the voteshare for each race was adding up correctly as some candidates were not picked up in the scrape.</li>
      <li><b>name_mappings.csv</b>: I created this file with a python script and some manual entry to map candidate names between all the other csv files - this enabled me to build out a sqlite database with all the csv files integrated together with key relationships.</li>
    </ol>
  </li>
  <li>plots/
      <ol>
        <li><b>House_GOP_ElectionStances.png</b>: This plot shows GOP House candidates by stance on the 2020 U.S. Presidential Election results </li>
        <li><b>Senate_GOP_ElectionStances.png</b>: This plot shows GOP Senate candidates by stance on the 2020 U.S. Presidential Election results</li>
        <li><b>House_ElectionDenier_Predictions.png</b>: This plot shows GOP House candidates that Fully Denied the 2020 U.S. Presidential Election results by chance of winning, incumbency.</li></li>
        <li><b>Senate_ElectionDenier_Predictions.png</b>: This plot shows GOP Senate candidates that Fully Denied the 2020 U.S. Presidential Election results by chance of winning, incumbency.</li>
        <li><b>House_ElectionDenier_Results.png</b>: This plot shows GOP House candidates that Fully Denied the 2020 U.S. Presidential Election results by chance of winning, incumbency, and race result.</li>
        <li><b>Senate_ElectionDenier_Results.png</b>: This plot shows GOP Senate candidates that Fully Denied the 2020 U.S. Presidential Election results by chance of winning, incumbency, and race result.</li>
      </ol>
  </li>
  <li><b>Election_Deniers.ipynb</b>: This is my Jupyter notebook file that contains the steps I took to answer my business questions following the CRISP-DM process.   circle_plotter.py and election_pipeline.py are imported into this notebook.</li>
  <li><b>circle_plotter.py</b>: This file contains classes created to generate circle plots, which I used as a visualization tool in my analysis.</li>
  <li><b>election_pipeline.py</b>: This file contains classes created to build a sqlite relational database from each csv file in the data folder. </li>
  <li><b>elections_erd.png</b>: This is this is the data model prior to integrating the data. I used it to map out the relationship between each csv file.</li>
  <li><b>elections_final_erd.png</b>: This is this is the data model after integrating the data. The data from each csv file was loaded into this table structure.</li>
  <li><b>usa_flag.jpg</b>: This is the image I used for my blog post which came from pixabay.com and does not require attribution.</li>
</ol>


## Summary of the results:
<ol>
    <li><b>Where did Republican (GOP) Midterm candidates stand on the results 2020 U.S. Presidential Election?</b>
        <ul>
             <li> I found the most common stance among GOP candidates in the House of Representatives was that candidates Fully Denied the
               results of the 2020 U.S. Presidential election - around <b>40%</b> of GOP candidates Fully Denied the election results. Only <b>27%</b> of candidates                  accepted the election results, but majority of those candidates added concerns or questions about Fraud. Around <b>a third</b> of GOP House candidates                  either did not comment on the election result, evaded the question when asked or were ambiguous in accepting or rejecting the results.
              </li>
              <li> In the Senate, Fully Denying the election results was not the common stance among GOP candidates - in fact, <b>61%</b> of GOP candidates accepted                      the election results though <b>half</b> of those candidates had questions or concerns about fraud, and only <b>22%</b> of candidates Fully Denied the election results.
              </li>
        </ul>
    </li>
   <li><b>How were Republican (GOP) candidates that fully-denied the election results projected to fare in the midterms?</b>
        <ul>
            <li>In the House, <b>127</b> out <b>170</b> (or about <b>75%</b>) of election denier candidates were favored to win, and <b>117</b> of those <b>127</b>                     candidates had at least a <b>95%</b> chance of winning. Many of the election denier candidates favored to win were incumbent candidates - out of the                   <b>127</b> election denier candidates favored to win <b>112</b> were incumbents. 
            </li>
            <li>In the Senate, <b>5</b> out of <b>8</b> (or <b>62%</b>) of Senate election denier candidates were favored to win, however, only <b>38%</b> had at least                 a 95% chance of winning. There were also not as many incumbent election denier Senate candidates - only <b>1</b> out of <b>8</b> election denier                       candidates in the Senate was an incumbent.
            </li>
       </ul>
    </li>
  <li><b>How did Republican (GOP) candidates that fully-denied the election results fare in the midterms?</b>
        <ul>
            <li>In the House, <b>125</b> out <b>170</b> (or about <b>74%</b>) of election denier candidates won their race. <b>110</b> out of <b>113</b> of election denier  incumbent candidates (or <b>97%</b>) won re-election, whereas only <b>15</b> out <b>57</b> (or <b>26%</b>) of non-incumbent election denier candidates won. 
            </li>
            <li>In the Senate, <b>5</b> out of <b>8</b> (or <b>62%</b>) of Senate election denier candidates won their race, including <b>4</b> non-incumbent candidates. 
            </li>
       </ul>
    </li>
    
## Link to Blog Post: https://medium.com/@jonathan.mi.collier/533c6e5318c2
## Sources used for this post:

[1]: “Reuters/Ipsos: Trump’s Coattails (04/02/2021).” Ipsos, Ipsos, 2 Apr. 2021, https://www.ipsos.com/sites/default/files/ct/news/documents/2021-04/topline_write_up_reuters_ipsos_trump_coattails_poll_-_april_02_2021.pdf. Accessed 10 Mar. 2023.

[2]: Yourish, Karen, et al. “The 147 Republicans Who Voted to Overturn Election Results.” The New York Times, The New York Times, 7 Jan. 2021, https://www.nytimes.com/interactive/2021/01/07/us/elections/electoral-college-biden-objectors.html.

## Datasets used for this post:

[1]: data/election-forecasts-2022 at master · fivethirtyeight/data (github.com)

[2]: data/election-deniers at master · fivethirtyeight/data (github.com)

[3]: Senate Midterm Election 2022: Live Updates, Results & Map (nbcnews.com)

[4]: House of Representatives Midterm Election 2022: Live Updates, Results & Map (nbcnews.com)
