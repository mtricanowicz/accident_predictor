# Traffic Impact Predictor App
Access app here: [https://accidentpredictor6156.streamlit.app/](https://accidentpredictor6156.streamlit.app/ "Traffic Impact Predictor")<br>
## About the app
App to accept user input with accident parameters and then use a classifier machine learning model to generate a predicted traffic impact severity. This app was created to satisfy the project requirement of DSBA-6156 ([accompanying presentation](https://drive.google.com/file/d/1Vj1fqX60gXV3cpbQYPe6Z-6KPvJiyIji/view?usp=sharing "PREDICTING TRAFFIC
IMPACT OF ACCIDENTS")) as part of the MS degree program in Data Science and Business Analytics at The University of North Carolina at Charlotte.<br><br>
EDA, data cleaning, data transformation and data preparation was performed as shown in [this data preparation notebook](https://drive.google.com/file/d/1rOPQBmF8NVpFWtm5bUert8D-OynTMege/view?usp=drive_link "Tricanowicz_DSBA6156_Project_preparation.ipynb").<br>
Model development and refinement was accomplished as shown in [this model building notebook](https://drive.google.com/file/d/1ptm-Hfa8PqtnDcnHQrgcJkTtjjiVyy8D/view?usp=drive_link "Tricanowicz_DSBA6156_Project_modeling.ipynb").<br>
Final model preparation for delivery to app was done in [this applet model notebook](https://drive.google.com/file/d/1Rj59Kkswu2-XO2YKqF1qT_VdCc2uuq4B/view?usp=drive_link "Tricanowicz_DSBA6156_Project_applet_model.ipynb").<br>

## How the app works
The current version of this app uses a VotingClassifier model with constituent models RandomForestClassifier and XGBClassifier trained on the following features: Start_Lat, Start_Lng, Temperature(F), Humidity(%), Pressure(in), Visibility(mi), Wind_Speed(mph), Traffic_Signal, Start_Month, Start_Day, Start_Hour.
The model was developed around the ['US Accidents (2016-2023)'](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents) dataset found on kaggle.
The dataset contains approximately 7.7 million accident records from the continental United States between the years 2016-2023 with 46 original features.
Undersampling, data cleaning, and feature selection was performed on the original dataset to prepare it for model development.<br><br>
This app provides a means for a user to input an accident location. The location and time of the input, as well as accompanying geographic and weather data, is fed into the model to generate a prediction. This app is designed to require as little user intervention as possible. A single click should be sufficient to obtain a prediction.<br>

This is accomplished by processing the user input as follows:
1. The user click generates a latitude and longitude value.
2. The lat/lon is processed by timzonefinder and pytz to determine the local time zone.
3. A timestamp is applied at time of click with the local timezone to generate local time of the event.
4. The lat/lon is processed by the Nominatim geocoder of geopy to generate the nearest address to the event location.
5. The lat/lon is processed by the OpenWeatherMap API to fetch the weather conditions for the location and time of the event.
6. The lat/lon is processed by the OpenStreetMap Overpass API to fetch whether a traffic signal is present within 400 m (approx 1/4 mile) of the event location.
7. The lat/lon is processed by the OpenStreetMap Overpass API to confirm whether it is a road to ensure it is a valid location to make a traffic impact prediction.
8. The processed data is then compiled into a dataframe as the input variables for the model.
9. The input dataframe is fed to the model to generate a severity prediction between 1 (least severe) and 4 (most severe).
10. The prediction and input variables are displayed by the app in a user friendly format. 
<br><br>

**Created by:**<br>
Michael Tricanowicz