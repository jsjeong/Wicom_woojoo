#import all the library needed
import numpy as np
from pyiotown_wicom import postprocess
#import pyiotown.post
from joblib import load, dump
from sklearn.ensemble import IsolationForest
import threading
import warnings
import sys

warnings.filterwarnings("ignore")

counter = 1

#thresholding value
threshold_waterlevel1 = 300
threshold_waterlevel2 = 3500
threshold_hum1_lower = 15
threshold_hum1_upper = 55
threshold_hum2_lower = 15
threshold_hum2_upper = 55
threshold_temp1_lower = 5
threshold_temp1_upper = 40
threshold_temp2_lower = 5
threshold_temp2_upper = 40
threshold_temp3_lower = 5
threshold_temp3_upper = 40

#sliding window setting
batch_size = 60 # 60 = 1 hour
train_number = 1440 # 1440 = 1 day

def train(): # for retraining model & overwriting model
    global arr_hum1, arr_hum2
    global arr_temp1, arr_temp2, arr_temp3
    global arr_waterlevel, arr_waterleak
    global arr_door, arr_fire

    #model initialization
    estimator = 100
    samples = 500
    randstate = 42
    outlier_fraction = 0.05
    
    model_hum1 = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=outlier_fraction)
    model_hum2 = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=outlier_fraction)
    model_temp1 = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=outlier_fraction)
    model_temp2 = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=outlier_fraction)
    model_temp3 = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=outlier_fraction)
    model_waterlevel = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=0.01)
    model_waterleak = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=0.01)
    model_fire = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=0.01)
    model_door = IsolationForest(n_estimators=estimator, max_samples=samples, random_state=randstate, contamination=0.01)
    
    #data preprocess
    arr_hum1 = arr_hum1.reshape(-1,1)
    arr_hum2 = arr_hum2.reshape(-1,1)
    arr_temp1 = arr_temp1.reshape(-1,1)
    arr_temp2 = arr_temp2.reshape(-1,1)
    arr_temp3 = arr_temp3.reshape(-1,1)
    arr_waterlevel = arr_waterlevel.reshape(-1,1)
    arr_waterleak = arr_waterleak.reshape(-1,1)
    arr_fire = arr_fire.reshape(-1,1)
    arr_door = arr_door.reshape(-1,1)

    #model training
    model_hum1.fit(arr_hum1)
    model_hum2.fit(arr_hum2)
    model_temp1.fit(arr_temp1)
    model_temp2.fit(arr_temp2)
    model_temp3.fit(arr_temp3)
    model_waterlevel.fit(arr_waterlevel)
    model_waterleak.fit(arr_waterleak)
    model_fire.fit(arr_fire)
    model_door.fit(arr_door)

    #save/overwrite model
    dump(model_hum1, 'model\model_hum1.joblib')
    dump(model_hum2, 'model\model_hum2.joblib')
    dump(model_temp1, 'model\model_temp1.joblib')
    dump(model_temp2, 'model\model_temp2.joblib')
    dump(model_temp3, 'model\model_temp3.joblib')
    dump(model_waterlevel, 'model\model_waterlevel.joblib')
    dump(model_waterleak, 'model\model_waterleak.joblib')
    dump(model_fire, 'model\model_fire.joblib')
    dump(model_door, 'model\model_door.joblib')
    print('Retraining is done')

def post_process(message):

    global arr_hum1, arr_hum2
    global arr_temp1, arr_temp2, arr_temp3
    global arr_waterlevel, arr_waterleak
    global arr_door, arr_fire
    global counter
    global model_hum1, model_hum2
    global model_temp1, model_temp2, model_temp3
    global model_waterlevel, model_waterleak
    global model_fire, model_door
    
    print(message)
    
    temp1 = np.array([message['data']['temp1']]).T
    temp2 = np.array([message['data']['temp2']]).T
    temp3 = np.array([message['data']['temp3']]).T
    hum1 = np.array([message['data']['hum1']]).T
    hum2 = np.array([message['data']['hum2']]).T
    water_level = np.array([message['data']['water_level']]).T
    water_leak = np.array([message['data']['water_leak']]).T
    door = np.array([message['data']['door']]).T
    fire = np.array([message['data']['fire']]).T
    
    print(counter)

    if counter == 1: #Using Initial model for the mode 1 & 2
        print("mode1")
        model_hum1 = load("model\model_hum1.joblib")
        model_hum2 = load("model\model_hum2.joblib")
        model_temp1 = load("model\model_temp1.joblib")
        model_temp2 = load("model\model_temp2.joblib")
        model_temp3 = load("model\model_temp3.joblib")
        model_waterlevel = load("model\model_waterlevel.joblib")
        model_waterleak = load("model\model_waterleak.joblib")
        model_fire = load("model\model_fire.joblib")
        model_door = load("model\model_door.joblib")
        counter +=1  

    elif counter<=train_number: 
        #keep using initial model until the data stored in array is enough
        print("mode2")
        counter +=1   

    elif counter == (train_number+1) : 
        #retrain the  model
        thread = threading.Thread(target=train)
        print("mode3:retrain")
        print(thread.is_alive())
        if thread.is_alive():
            print('thread still running')          
        else:
            print('thread is starting')
            thread.start()
        counter += 1
        thread.join()    
    
    elif counter == (train_number+2):
        print("mode4:load retrain model")
        model_hum1 = load("model\model_hum1.joblib")
        model_hum2 = load("model\model_hum2.joblib")
        model_temp1 = load("model\model_temp1.joblib")
        model_temp2 = load("model\model_temp2.joblib")
        model_temp3 = load("model\model_temp3.joblib")
        model_waterlevel = load("model\model_waterlevel.joblib")
        model_waterleak = load("model\model_waterleak.joblib")
        model_fire = load("model\model_fire.joblib")
        model_door = load("model\model_door.joblib")
        counter += 1

    elif counter < (train_number + batch_size): 
        #sliding window method
        print("mode5")
        counter +=1
    
    else: #optimize the array size of the sliding window
        counter = (train_number+1)
        print("mode6:optimize array size")
        arr_hum1 = arr_hum1[-train_number:]
        arr_hum2 = arr_hum2[-train_number:]
        arr_temp1 = arr_temp1[-train_number:]
        arr_temp2 = arr_temp2[-train_number:]
        arr_temp3 = arr_temp3[-train_number:]
        arr_waterlevel = arr_waterlevel[-train_number:]
        arr_waterleak = arr_waterleak[-train_number:]
        arr_fire = arr_fire[-train_number:]
        arr_door = arr_door[-train_number:]

    #input data to the window
    arr_hum1 = np.append(arr_hum1,hum1)
    arr_hum2 = np.append(arr_hum2,hum2)
    arr_temp1 = np.append(arr_temp1,temp1)
    arr_temp2 = np.append(arr_temp2,temp2)
    arr_temp3 = np.append(arr_temp3,temp3)
    arr_waterlevel = np.append(arr_waterlevel,water_level)
    arr_waterleak = np.append(arr_waterleak,water_leak)
    arr_fire = np.append(arr_fire,fire)
    arr_door = np.append(arr_door,door)

    #preprocess the data for anomaly detection
    newhum1 = hum1.reshape(1,-1)
    newhum2 = hum2.reshape(1,-1)
    newtemp1 = temp1.reshape(1,-1)
    newtemp2 = temp2.reshape(1,-1)
    newtemp3 = temp3.reshape(1,-1)
    newwater_level = water_level.reshape(1,-1)
    newwater_leak = water_leak.reshape(1,-1)
    newfire = fire.reshape(1,-1)
    newdoor = door.reshape(1,-1)
    
    #anomaly detection / Isolation Forest Prediction
    anomaly_score_hum1 = model_hum1.decision_function(newhum1)
    anomaly_score_hum2 = model_hum2.decision_function(newhum2)
    anomaly_score_temp1 = model_temp1.decision_function(newtemp1)
    anomaly_score_temp2 = model_temp2.decision_function(newtemp2)
    anomaly_score_temp3 = model_temp3.decision_function(newtemp3)
    anomaly_score_waterlevel = model_waterlevel.decision_function(newwater_level)
    anomaly_score_waterleak = model_waterleak.decision_function(newwater_leak)
    anomaly_score_fire = model_fire.decision_function(newfire)
    anomaly_score_door = model_door.decision_function(newdoor)

    anomalies_hum1 = model_hum1.predict(newhum1)
    anomalies_hum2 = model_hum2.predict(newhum2)
    anomalies_temp1 = model_temp1.predict(newtemp1)
    anomalies_temp2 = model_temp2.predict(newtemp2)
    anomalies_temp3 = model_temp3.predict(newtemp3)
    anomalies_waterlevel = model_waterlevel.predict(newwater_level)
    anomalies_waterleak = model_waterleak.predict(newwater_leak)
    anomalies_fire = model_fire.predict(newfire)
    anomalies_door = model_door.predict(newdoor)

    #clustering between normal & abnormal
    if anomalies_hum1 > 0 and float(hum1[0]) > threshold_hum1_lower and float(hum1[0]) < threshold_hum1_upper:
        status_hum1 = 'normal'
    else:
        status_hum1 = 'abnormal'
    
    if anomalies_hum2 > 0 and float(hum2[0]) > threshold_hum2_lower and float(hum2[0]) < threshold_hum2_upper:
        status_hum2 = 'normal'
    else:
        status_hum2 = 'abnormal'

    if anomalies_temp1 > 0 and float(temp1[0]) > threshold_temp1_lower and float(temp1[0]) < threshold_temp1_upper:
        status_temp1 = 'normal'
    else:
        status_temp1 = 'abnormal'

    if anomalies_temp2 > 0 and float(temp2[0]) > threshold_temp2_lower and float(temp2[0]) < threshold_temp2_upper:
        status_temp2 = 'normal'
    else:
        status_temp2 = 'abnormal'

    if anomalies_temp3 > 0 and float(temp3[0]) > threshold_temp3_lower and float(temp3[0]) < threshold_temp3_upper:
        status_temp3 = 'normal'
    else:
        status_temp3 = 'abnormal'

    if anomalies_waterlevel > 0 and float(water_level[0]) > threshold_waterlevel1 and float(water_level[0]) < threshold_waterlevel2:
        status_waterlevel = 'normal'
    else:
        status_waterlevel = 'abnormal'

    if anomalies_waterleak > 0 and float(water_leak[0]) == 0:#thresholding for binary sensor
        status_waterleak = 'normal'
    else:
        status_waterleak = 'abnormal/isflood'
    
    if anomalies_fire > 0 and float(fire[0]) == 0: #thresholding for binary sensor
        
        status_fire = 'normal'
    else:
        status_fire = 'abnormal/fire'

    if anomalies_door > 0 and float(door[0]) == 0: #thresholding for binary sensor
        status_door = 'normal'
    else:
        status_door = 'abnormal/open'

    changedata = {}

    #store the data in order to send it back to IoT.own
    changedata['status_temp1'] = status_temp1
    changedata['status_temp2'] = status_temp2
    changedata['status_temp3'] = status_temp3
    changedata['status_hum1'] = status_hum1
    changedata['status_hum2'] = status_hum2
    changedata['status_water_level'] = status_waterlevel
    changedata['status_water_leak'] = status_waterleak
    changedata['status_door'] = status_door
    changedata['status_fire'] = status_fire

    changedata['temp1'] = float(temp1[0])
    changedata['temp2'] = float(temp2[0])
    changedata['temp3'] = float(temp3[0])
    changedata['hum1'] = float(hum1[0])
    changedata['hum2'] = float(hum2[0])
    changedata['water_level'] = float(water_level[0])
    changedata['water_leak'] = float(water_leak[0])
    changedata['door'] = float(door[0])
    changedata['fire'] = float(fire[0])
    
    changedata['anomaly_score_temp1'] = round(float(anomaly_score_temp1[0]),2)
    changedata['anomaly_score_temp2'] = round(float(anomaly_score_temp2[0]),2)
    changedata['anomaly_score_temp3'] = round(float(anomaly_score_temp3[0]),2)
    changedata['anomaly_score_hum1'] = round(float(anomaly_score_hum1[0]),2)
    changedata['anomaly_score_hum2'] = round(float(anomaly_score_hum2[0]),2)
    changedata['anomaly_score_waterlevel'] = round(float(anomaly_score_waterlevel[0]),2)
    changedata['anomaly_score_waterleak'] = round(float(anomaly_score_waterleak[0]),2)
    changedata['anomaly_score_door'] = round(float(anomaly_score_door[0]),2)
    changedata['anomaly_score_fire'] = round(float(anomaly_score_fire[0]),2)
 
    message['data'] = changedata
    print(changedata)
    return message

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} [URL] [name] [token]")
        exit(1)
        
    arr_hum1 = np.array([[]])
    arr_hum2 = np.array([[]])
    arr_temp1 = np.array([[]])
    arr_temp2 = np.array([[]])
    arr_temp3 = np.array([[]])
    arr_waterlevel = np.array([[]])
    arr_waterleak = np.array([[]])
    arr_door = np.array([[]])
    arr_fire = np.array([[]])
    postproc_name = 'PostProcessExample3'
    url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    postprocess(url,postproc_name,post_process, username, password)
    #pyiotown.post.postprocess(url,postproc_name,post_process, username, password)
