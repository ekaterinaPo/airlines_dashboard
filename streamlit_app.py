import streamlit as st
import pandas as pd
#import shap
import matplotlib.pyplot as plt
import numpy as np
import boto3
AWS_S3_BUCKET = "airlines-dashboard"

st.title("Airlines Tweets App")
st.subheader("Sentiment Analysis!")
st.write('---')

# Loads the Dataset
def results_fromS3():
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key="results/results.csv")
    df = pd.read_csv(response.get("Body"))
    return df

#df_folder = pd.read_csv('results.csv')
df = results_fromS3()
df_ = df.rename(columns={"query": "airline"})
df_1 = df_[0:25]
df_2 = df_[25:]
df_2["date"] = "2022-10-01"
df_1["date"] = "2022-09-30"
df = pd.concat([df_1, df_2])
#first graph
st.bar_chart(df["airline"].value_counts())
"""
df["airline"].value_counts().plot.bar()

#second graph
labels = 'Aircanada', 'WestJet', 'Swoop'
a = df["airline"].value_counts()
sizes = a.values
#sizes = [15, 30, 45, 10]
explode = (0.05, 0.05, 0.05)  # only "explode" the 2nd slice (i.e. 'Hogs')
colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(a)))

fig1, ax1 = plt.subplots()
ax1.pie(sizes, colors=colors,explode=explode, labels=labels, autopct='%1.1f%%',
        shadow=True, startangle=90)
ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

plt.show()
#dataset example
print("Train data shape: ", df.shape)
# sample rows to visualize
df.head()

#WORD OF BAGS
from sklearn.base import BaseEstimator
import nltk
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

#4 graph
train = df
sentence_lengths = [len(sentence) for sentence in train['text']]
plt.hist(sentence_lengths,500)
plt.xlabel('Length of comments')
plt.show()
"""