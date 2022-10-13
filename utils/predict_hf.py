from multiprocessing.connection import Client
from threading import local
import pandas as pd
from transformers import AutoModelForSequenceClassification, RobertaForSequenceClassification
from transformers import TFAutoModelForSequenceClassification
from transformers import AutoTokenizer, RobertaTokenizer
import numpy as np
from scipy.special import softmax
import csv
#import urllib.request
import torch
from botocore.exceptions import ClientError
import datetime

from utils.getdata import download_fromS3, upload_toS3
import utils.config
import boto3
import os
from pathlib import Path

labels = ['negative', 'neutral', 'positive']
AWS_S3_BUCKET = "airlines-dashboard"

s3_client = boto3.client("s3")
s3_res = boto3.resource("s3")

def dataset(n = None, dir_name = "data", file_name = "data.csv"):
    df = download_fromS3(dir_name = dir_name, file_name = file_name)
    if n is None: n = len(df)
    df_sample = df.sample(n = n)
    return df_sample

def get_list_to_predict():
    # get list of files to process
    try:
        obj = s3_res.Object(AWS_S3_BUCKET, "data/to_process.txt")
        files_list = obj.get()["Body"].read().decode("utf-8")
    except ClientError:
        files_list = []
    
    return files_list

#download model from S3 to local_dir
def get_download_model():
    model_type = "cardiffnlp/twitter-roberta-base-sentiment"
    local_dir = f"./{model_type}"
    # if this dir doesn't exist or is empty
    if not Path(local_dir).is_dir() or (not any(Path(local_dir).iterdir())):
        Path(local_dir).mkdir(parents = True, exist_ok = True)
        print("Downloading model files... ", end = "")
        s3 = boto3.resource("s3")
        my_bucket = s3.Bucket("airlines-dashboard")
        for obj in my_bucket.objects.filter(Prefix=f"model/{model_type}"):
            path, filename = os.path.split(obj.key)
            local_file = os.path.join(local_dir, filename)
            #my_bucket.download_file(obj.key, filename)
            my_bucket.download_file(obj.key, local_file)
        print("done.")

    #tokenizer = AutoTokenizer.from_pretrained(local_dir)
    tokenizer = RobertaTokenizer.from_pretrained(local_dir)
    #model = AutoModelForSequenceClassification.from_pretrained(pretrained_model_name_or_path = local_dir)
    model = RobertaForSequenceClassification.from_pretrained(local_dir)

    return model, tokenizer


def preprocess(text):
    new_text = []
    for t in text.split(" "):
        t = '@user' if t.startswith('@') and len(t) > 1 else t
        t = 'http' if t.startswith('http') else t
        new_text.append(t)
    return " ".join(new_text)


def get_prediction(n=None):
    # get list of files to process
    files_list = get_list_to_predict()
    # get dataset of master predictions
    df_master = dataset(dir_name = "results", file_name = "results.csv")
    # backup current results file
    cur_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
    file_name = f"results_{cur_time}.csv"
    df_master.to_csv(file_name, index=False, header=True)
    upload_toS3(file_name, "results")
    # get predictions for all unprocessed files
    for f in files_list:
        df_sample = dataset(n=n,  file_name = f)
        model, tokenizer = get_download_model()
        preprocess_text = df_sample["text"].map(preprocess)
        encoded_all = tokenizer(list(preprocess_text.values), return_tensors = "pt", truncation = True, padding = True, max_length = 256)
        output_all = model(**encoded_all)
        label_ids = torch.argmax(output_all.logits, axis = 1).detach().numpy()
        df_sample["labels"] = [labels[x] for x in label_ids]
        df_master = pd.concat([df_master, df_sample], ignore_index = True, sort = False)
    # df_sample.to_csv("results.csv", index = False, header = True)
    df_master = df_master.drop_duplicates(subset = "tweet_id")
    # save predictions to file
    df_master.to_csv("results.csv", index = False)
    upload_toS3("results.csv", "results")
    # clear list of files to download
    s3_res.Object(AWS_S3_BUCKET, "data/to_predict.txt").put(Body = "")
    #return df_sample

