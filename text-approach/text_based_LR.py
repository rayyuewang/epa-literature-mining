# -*- coding: utf-8 -*-
"""text_based_LR+Active Learning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12NUXZ_4RxcQ26xrlTM3139-b2EPxWE25
"""

import re
import string
import nltk
import random

import pandas as pd
import numpy as np

from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from statistics import mean

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, HashingVectorizer
from sklearn.linear_model import LogisticRegression

import matplotlib as mpl 
import matplotlib.pyplot as plt

"""#File import"""

import csv
filepath = './s2013.csv'
s2013 = pd.read_csv(filepath,engine='python')
filepath_2 = './s2020.csv'
s2020 = pd.read_csv(filepath_2,engine='python',error_bad_lines=False)

# quoting=csv.QUOTE_NONE,error_bad_lines=False,
# print('data size:', len(s2013))

"""#Convert abstract and construct features



"""

# vectorizer = HashingVectorizer(stop_words = None, ngram_range = (1,3)).fit(s2013_abstracts)
vectorizer = TfidfVectorizer(stop_words = None, ngram_range = (1,3)).fit(s2013['ABSTRACT'].values.astype('U'))

# construct sparse feature matrix
# params:
#     df: dataframe, with 'original' and 'edit' columns
#     vectorizer: sklearn text vectorizer, either TfidfVectorizer or Countvectorizer 
# return:
#     M: a sparse feature matrix that represents df's textual information (used by a predictive model)

def construct_feature_matrix(df, vectorizer):
    abstract = df['ABSTRACT'].apply(lambda x: np.str_(x)).tolist()
  
    # here the dimensionality of X is len(df) x |V|
    X = vectorizer.transform(abstract)
    # T = scipy.sparse.hstack([X,Y,Z])
    

    return X

train_Y = s2013['CITED']
train_X = construct_feature_matrix(s2013, vectorizer)
print(train_X.shape)
test_X = construct_feature_matrix(s2020, vectorizer)
print(test_X.shape)

model = LogisticRegression(penalty='l2').fit(train_X, train_Y)
test_Y_hat = model.predict_proba(test_X)

test_Y_hat

prob=[]
# index=[]
for i in range(0,len(test_Y_hat)):
  prob.append(test_Y_hat[i][1])
#   index.append(i)

def merge(list1, list2, list3, list4):
    merged_list = []
    for i in range(max((len(list1), len(list2),len(list3),len(list4)))):
        while True:
            try:
                tup = (list1[i], list2[i], list3[i],list4[i])
            except IndexError:
                if len(list3) > len(list2):
                    list2.append('')
                    tup = (list1[i], list2[i],list3[i],list4[i])
                elif len(list3) < len(list2):
                    list3.append('')
                    tup = (list1[i], list2[i],list3[i],list4[i])
                continue
            merged_list.append(tup)
            break
    return merged_list

#create list of tuples and sort
merged_list = merge(s2020['REFERENCE_ID'],s2020['PMID'],s2020['CITED'],prob)
merged_list.sort(key=lambda y: y[3],reverse=True)
print(merged_list[0:10])

# df = pd.DataFrame(merged_list)  
# df.to_csv('result.csv')

"""#Calculate Recall"""

def calculate_recall(filepath,pmid_only,num):
  #filepath is a list
  pair = []
  filepath.sort(key=lambda y: y[3],reverse=True)
  if pmid_only == True:
    filepath=list(filter(lambda c: np.isnan(c[1]) == False, filepath))
  for i in range(1,len(filepath),num):
    tp = 0
    fn = 0
    for j in range(1,i):
      if filepath[j][2] == 1:
        tp += 1
    for k in range(i+1,len(filepath)):
      if filepath[k][2] == 1:
        fn += 1
    pair.append((i,tp/(tp+fn)))
  return pair

recall=calculate_recall(merged_list,True,1000)
recall

"""#Creating graphs"""

x_axis = []
y_axis = []
for i in range(0,len(recall)):
  x_axis.append(recall[i][0])
  y_axis.append(recall[i][1])

x = [i for i in range(len(y_axis)) if y_axis[i] > 0.95]
initial=x[0]/len(y_axis)
initial

figure = plt.figure() 
axes1 = figure.add_subplot(1,1,1)  
axes1.plot(x_axis,y_axis) 
# plt.title('As a whole')
plt.scatter([20010],[0.95],s=25,c='r') 
plt.plot([0,20010],[0.95,0.95],c='b',linestyle='--')
plt.plot([20010,20010],[0,0.95],c='b',linestyle='--')
plt.text(20010+0.15,0.95-0.12,'recall@k=95%',ha='center',va='bottom',fontsize=10.5)
plt.scatter([12010],[0.90],s=25,c='r') 
plt.plot([0,12010],[0.90,0.90],c='b',linestyle='--')
plt.plot([12010,12010],[0,0.90],c='b',linestyle='--')
plt.text(12010+0.15,0.90-0.12,'recall@k=90%',ha='center',va='bottom',fontsize=10.5)
ax = plt.gca()
ax.spines['top'].set_color('none')
ax.spines['right'].set_color('none')
ax.xaxis.set_ticks_position('bottom')
ax.yaxis.set_ticks_position('left')
ax.spines['bottom'].set_position(('data',0))
ax.spines['left'].set_position(('data',0))
figure.show()

"""#Making it iterative"""

n=100
iter=20
index_list=[0]
percentile_list=[initial]
for j in range(1,iter):
  uncertain=[]
  m = mean([item[3] for item in merged_list])
  for i in range(0,len(merged_list)):
    if merged_list[i][3] <= m+0.05 and merged_list[i][3] >= m-0.05:
      uncertain.append(merged_list[i][0])
  uncertain_sampled = random.sample(uncertain,n)

  for i in range(1,len(uncertain_sampled)):
    for j in range(1,len(s2020)):
      if s2020['REFERENCE_ID'][j] == uncertain_sampled[i]:
        s2013=s2013.append(s2020.iloc[i])

  train_Y = s2013['CITED']
  train_X = construct_feature_matrix(s2013, vectorizer)
  test_X = construct_feature_matrix(s2020, vectorizer)

  model = LogisticRegression(penalty='l2').fit(train_X, train_Y)
  test_Y_hat = model.predict_proba(test_X)

  prob=[]
  # index=[]
  for i in range(0,len(test_Y_hat)):
    prob.append(test_Y_hat[i][1])
    # index.append(i)
  merged_list=merge(s2020['REFERENCE_ID'],s2020['PMID'],s2020['CITED'],prob)
  merged_list.sort(key=lambda y: y[3],reverse=True)
  # merged_list = merge(index,prob,s2020['CITED'])
  # merged_list.sort(key=lambda y: y[1],reverse=True)

  recall=calculate_recall(merged_list,1000)
  x_axis = []
  y_axis = []
  for i in range(0,len(recall)):
    x_axis.append(recall[i][0])
    y_axis.append(recall[i][1])

  x = [i for i in range(len(y_axis)) if y_axis[i] > 0.95]
  percentile=x[0]/len(y_axis)
  percentile_list.append(percentile)
  index_list.append(j*n)

percentile_list

figure = plt.figure() 
axes1 = figure.add_subplot(1,1,1)  
axes1.plot(index_list,percentile_list) 
# plt.title('As a whole')
# plt.scatter([94001],[0.95],s=25,c='r') 
# plt.plot([0,1900],[0.5,0.5],c='b',linestyle='--')
ax = plt.gca()
ax.spines['top'].set_color('none')
ax.spines['right'].set_color('none')
ax.xaxis.set_ticks_position('bottom')
ax.yaxis.set_ticks_position('left')
# ax.set_ylim(ymin=0,ymax=1)
figure.show()