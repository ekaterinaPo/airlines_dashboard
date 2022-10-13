import utils.config
import csv
import tweepy
import time
import datetime
import requests
import pandas as pd
from botocore.exceptions import ClientError
import boto3

s3_client = boto3.client("s3")
s3_res = boto3.resource("s3")

AWS_S3_BUCKET = "airlines-dashboard"
#s3 = boto3.resource('s3')

def get_tweets(query):#add query = @aircanada, @westjet, @flyswoop
    tweets = []
    client = tweepy.Client(utils.config.TWITTER_BEARER_TOKEN)
    #download tweets
    # date_range = [datetime.datetime.fromordinal((datetime.datetime.now().date() - 
    #                                               datetime.timedelta(days = x)).toordinal()) for x in range(2, 6)]
    # date_range = [(x, x + datetime.timedelta(days = 1)) for x in date_range]
    # for start_time, end_time in date_range:
    def get_date(days_before):
        dt = datetime.date.today() - datetime.timedelta(days = days_before)
        dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
        return dt

    start_time = get_date(2)
    end_time = get_date(1)
    
    resp = client.search_recent_tweets(query = query, max_results = 100, #user_fields = ["id", "name", "username"], 
                                        start_time = start_time, end_time = end_time)
    #resp = client.search_recent_tweets(query = "@aircanada", max_results = 100, start_time = date_param)
    tweets.extend(resp.data)
    # time.sleep(1)
    return tweets


def download_fromS3(dir_name = "data", file_name = "data.csv"):
    #s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=f"{dir_name}/{file_name}}")
    df = pd.read_csv(response.get("Body"))
    return df


def upload_toS3(file_name, folder):
    #s3_client = boto3.client("s3")
    s3_client.upload_file(f"{file_name}", AWS_S3_BUCKET, f"{folder}/{file_name}")

def add_to_history(file_name):
    to_predict_file_name = "data/to_predict.txt"
    # download / open from S3 "to_predict.txt". If it doesn't exist, do nothing
    try:
        obj = s3_client.get_object(Bucket = AWS_S3_BUCKET, Key = to_predict_file_name) #s3_res.Object(AWS_S3_BUCKET, "data/to_predict.txt")
        to_predict = obj["Body"].read()
    except ClientError:
        to_predict = ""

    # append file_name to "to_predict.txt"
    to_predict += f"\n{file_name}"

    # save "to_predict.txt" to S3
    s3_res.Object(AWS_S3_BUCKET, to_predict_file_name).put(Body = to_predict)

def get_df(tweets, query):
    #make data frame
    df_update = pd.DataFrame([{k: x.data[k] for k in ["id", "text"]} for x in tweets])
    df_update['query'] = query
    today = datetime.date.today()
    df_update['date'] = today
    df_update = df_update.rename(columns = {"id": "tweet_id"})
    return df_update

def save_append_to_df(df_update):
    #open existing csv file, add new rows and delete duplicated id
    #df = pd.read_csv("data.csv")
    df = download_fromS3()
    # make sure we leave only the needed columns
    df = df[["tweet_id", "text", "query","date"]]
    #save old version 
    cur_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    file_name = f"data_{cur_time}.csv"
    df.to_csv(file_name, index=False, header=True)
    upload_toS3(file_name, "data")
    #create a new updated dataframe
    df_new = pd.concat([df, df_update], ignore_index=True)
    #df_new = df_new.drop_duplicates(subset="tweet_id")
    #save new data to file
    df_new.to_csv('data.csv', index=False, header=True)
    df_from_file = pd.read_csv('data.csv')
    df_from_file = df_from_file.drop_duplicates(subset = "tweet_id")
    df_from_file.to_csv("data.csv", index = False, header = True)
    upload_toS3("data.csv", "data")
    
    return df_from_file

def save_to_s3(df):
    cur_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    file_name = f"data_{cur_time}.csv"
    df.to_csv(file_name, index = False, header = True)
    # upload the new file to S3
    upload_toS3(file_name, "data")
    # save the file to history
    add_to_history(file_name)


def load_data():#@aircanada, @westjet, @flyswoop
    airlines = ["aircanada", "westjet", "flyswoop"]#parameters that can be changed
    for i in airlines:
        tweets = get_tweets(query = f"@{i}")
        #print(f"{i}: ",len(tweets))
        df_update = get_df(tweets, query = f"{i}" )
        #print(f"{i}: ",len(df_update))
        #df_from_file = save_append_to_df(df_update)
        save_to_s3(df_update)
        #print(f"{i}: ",len(df_from_file))
