import pandas as pd
import plotly.express as px
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import argparse

#ArgParse
parser = argparse.ArgumentParser(prog = 'housing.py', description = 'This program estimates the price of a house in Palo Alto, CA given the square footage of a home.')
parser.add_argument('sqft', type = int, metavar = '<int>', help = 'Square footage of the house')
parser.add_argument('bed', type = int, metavar = '<int>', help = 'Number of bedrooms in the house')
parser.add_argument('bath', type = float, metavar = '<float>', help = 'Number of bathrooms in the house')
arg = parser.parse_args()

def __data_exploration():
    housing_data = pd.read_csv('paloalto.csv') #Make Pandas dataframe from the housing data
    """ #Printing the data frame
    print(housing_data)
    print(housing_data.info())
    print(housing_data.sqft.info())
    """
    """ #Histogram of the house prices
    fig = px.histogram(housing_data, x = 'price', marginal = 'box', nbins = 30, title = 'Distribution of House Prices')
    fig.update_layout(bargap=0.1)
    fig.show()
    """
    """ #Good linear correlation between square footage and house price
    fig = px.scatter(housing_data, x = 'sqft', y = 'price', opacity = 0.8, hover_data = ['bath'], title = 'Price vs. Sqft')
    fig.update_traces(marker_size = 5)
    fig.show() #plotting
    """
    """ #Weak correlation between bedroom data and house price, but seems to still contribute
    fig = px.scatter(housing_data, x = 'bedroom', y = 'price', opacity = 0.8, hover_data = ['bath'], title = 'Price vs. Sqft')
    fig.update_traces(marker_size = 5)
    fig.show() #plotting
    """
    """ #Similar to the bedroom data, there is a weak correlation, but seems to still contribute
    fig = px.scatter(housing_data, x = 'bath', y = 'price', opacity = 0.8, hover_data = ['bath'], title = 'Price vs. Sqft')
    fig.update_traces(marker_size = 5)
    fig.show() #plotting
    """
    """ #Root mean square deviation from the trendline when looking at the input data was 1451147.23
    inputs = housing_data[['sqft']]
    targets = housing_data['price']
    model = LinearRegression()
    model.fit(inputs, targets)
    predictions = model.predict(inputs)
    loss = rmse(targets, predictions)
    print(f'Root Mean Squared Loss when running regression with only sqft: {loss:.2f}')
    """
    """ #Root mean square deviation from the trendline does not change much when accounting for the bedrooms: 1444697.02
    inputs = housing_data[['sqft', 'bedroom']]
    targets = housing_data['price']
    model = LinearRegression()
    model.fit(inputs, targets)
    predictions = model.predict(inputs)
    loss = rmse(targets, predictions)
    print(f'Root Mean Squared Loss when running regression with sqft and : {loss:.2f}')
    """
    """ #Root mean square deviation from the trendline does not change much when accounting for the bathrooms: 1444687.49 (changed by <10)
    inputs = housing_data[['sqft', 'bedroom', 'bath']]
    targets = housing_data['price']
    model = LinearRegression()
    model.fit(inputs, targets)
    predictions = model.predict(inputs)
    loss = rmse(targets, predictions)
    print(f'Root Mean Squared Loss when running regression with sqft and : {loss:.2f}')
    """
    """
    The contribution of square footage of a house to the price is the most significant.
    The number of bedrooms and bathrooms has a miniscule impact on the model's accuracy.
    """

def rmse(targets, predictions):
    return np.sqrt(np.mean(np.square(targets - predictions)))

def main():
    #Make the model
    housing_data = pd.read_csv('paloalto.csv')
    inputs = housing_data[['sqft', 'bedroom', 'bath']]
    targets = housing_data['price']
    model = LinearRegression(positive = True)
    model.fit(inputs, targets)
    prediction = model.predict([[arg.sqft, arg.bed, arg.bath]])
    print(f'The estimated price of a house with {arg.sqft} square feet in area, {arg.bed} bedrooms, and {arg.bath} bathrooms in Palo Alto is ${prediction[0]:.2f}')


if __name__ == '__main__':
    #__data_exploration()
    main()