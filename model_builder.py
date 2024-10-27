# Basic libraries
import numpy as np
import pandas as pd
import pickle

# Statistics libraries
from sklearn import model_selection, metrics, tree, linear_model, ensemble
from sklearn.experimental import enable_halving_search_cv
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV, HalvingGridSearchCV
from sklearn.preprocessing import MinMaxScaler, StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_graphviz, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report, make_scorer, f1_score, accuracy_score, precision_score, recall_score, roc_curve, roc_auc_score, ConfusionMatrixDisplay

# Import prepared model data set
model_data = pd.read_csv("model_applet_data.csv")
# Remove "Unnamed: 0" column from data if it is present
model_data = model_data.drop(columns="Unnamed: 0", errors="ignore")

# Import the optimized model features
model_features = pd.read_csv("model_features.csv")
# Remove "Unnamed: 0" column from data if it is present
model_features = model_features.drop(columns="Unnamed: 0", errors="ignore")

# Import the optimized model parameters
model_parameters = pd.read_csv("model_parameters.csv")
# Remove "Unnamed: 0" column from data if it is present
model_parameters = model_parameters.drop(columns="Unnamed: 0", errors="ignore")
# Replace Null entries with None as this is the proper input for the hyperparameter
for i in range(0, len(model_parameters.columns)):
    if model_parameters[model_parameters.columns[i]].isna().any():
        model_parameters[model_parameters.columns[i]]=None

# Set a random state value to be the value used to optimize the model
random_state = model_parameters["random_state"][0]

# Set a training set proportion value to be used throughout.
train_size = 0.8

# Categorical columns identified as any non-numeric column in the model features set
cat_columns = model_data.dtypes.index[(model_data.dtypes!=np.int64) & (model_data.dtypes!=np.float64) & (model_data.dtypes!=bool)].values

# Independent variables
X = pd.get_dummies(model_data, columns=cat_columns, drop_first=True).drop(["Severity"], axis=1)
feature_names = X.columns

# Target variables
y = model_data["Severity"]

# Create training and testing splits for models
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=train_size, random_state=random_state)

# Instantiate the random forest to use the optimized model hyperparameters
rf = RandomForestClassifier(
    bootstrap=model_parameters["bootstrap"][0],
    ccp_alpha=model_parameters["ccp_alpha"][0],
    class_weight=model_parameters["class_weight"][0],
    criterion=model_parameters["criterion"][0],
    max_depth=model_parameters["max_depth"][0],
    max_features=model_parameters["max_features"][0],
    max_leaf_nodes=model_parameters["max_leaf_nodes"][0],
    max_samples=model_parameters["max_samples"][0],
    min_impurity_decrease=model_parameters["min_impurity_decrease"][0],
    min_samples_leaf=model_parameters["min_samples_leaf"][0],
    min_samples_split=model_parameters["min_samples_split"][0],
    min_weight_fraction_leaf=model_parameters["min_weight_fraction_leaf"][0],
    n_estimators=model_parameters["n_estimators"][0],
    n_jobs=model_parameters["n_jobs"][0],
    oob_score=model_parameters["oob_score"][0],
    random_state=model_parameters["random_state"][0],
    verbose=model_parameters["verbose"][0],
    warm_start=model_parameters["warm_start"][0]
    )

# Fit the model
model = rf.fit(X_train, y_train)

#with open('applet_model.pkl', 'wb') as file:
#    pickle.dump(model, file)