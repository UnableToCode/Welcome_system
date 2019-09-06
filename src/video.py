#this file is used to read emddings and captures frames
#every 0.5 second a frame is captured and all the ids（in the format of string） is stored in act_list
import cv2
import os
import numpy as np
import tensorflow as tf

import json
import time
import threading
from tensorflow.python.platform import gfile
from src.align import detect_face

send_sig = False
#network for mtcnn, set them as global parm to avoid re-load model
MODEL_PATH=r'./model/20180402-114759/20180402-114759.pb'
EMD_PATH=r'./proj/face_emddings'
def load_emddings():
    #read emddings and labels from EMD_PATH
    #input:
    # null
    #output:
    #emd_list python list ,shape(?,512),contain face emddings of ? person
    #label_list python list, shape(?,1),contain labels of ? person
    #notice:idx of emd and labels are the same(e.g. emd_list[0]conatins label_list[0] person's emddings)
    emd_list = []
    label_list = []
    for file_names in os.listdir(EMD_PATH):
        print("load %s file"%file_names)
        with open(os.path.join(EMD_PATH, file_names), 'r') as load_f:
            temp_emd = json.load(load_f)
        # print(temp_emd)
        emd_list.append(np.array(temp_emd))
        label_list.append(file_names[0:-4])
    return emd_list, label_list
def prewhiten(x):
    #preprocess of a face
    #used in align
    mean = np.mean(x)
    std = np.std(x)
    std_adj = np.maximum(std, 1.0 / np.sqrt(x.size))
    y = np.multiply(np.subtract(x, mean), 1 / std_adj)
    return y
def load_model(model,sess, input_map=None):
    #load model from caffe model to create mtcnn model
    #load model from a tensorflow pb file to create facenet model
    gpu_options = tf.GPUOptions()
    gpu_options.allow_growth = True
    pnet, rnet, onet = detect_face.create_mtcnn(sess, None)
    model_exp = os.path.expanduser(MODEL_PATH)
    print('Model filename: %s' % model_exp)
    with gfile.FastGFile(model_exp, 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, input_map=input_map, name='')
    return pnet,rnet,onet
def load_and_align_data(img, image_size, margin,p,r,o):
    minsize = 20  # minimum size of face
    threshold = [0.6, 0.7, 0.7]  # three steps's threshold
    factor = 0.709  # scale factor
    img_list = []
    img_size = np.asarray(img.shape)[0:2]
    bounding_boxes, _ = detect_face.detect_face(img, minsize, p, r, o, threshold, factor)
    if len(bounding_boxes) < 1:
        print("can't detect face, remove ")
        return False, np.array([])
    else:
        det = np.squeeze(bounding_boxes[0, 0:4])
        bb = np.zeros(4, dtype=np.int32)
        bb[0] = np.maximum(det[0] - margin / 2, 0)
        bb[1] = np.maximum(det[1] - margin / 2, 0)
        bb[2] = np.minimum(det[2] + margin / 2, img_size[1])
        bb[3] = np.minimum(det[3] + margin / 2, img_size[0])
        cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]
        aligned = cv2.resize(cropped, (image_size, image_size))
        prewhitened = prewhiten(aligned)
        img_list.append(prewhitened)
    images = np.stack(img_list)
    return True, images
def compare(sess,faces,emd_list,label_list):
    #project 160*160*3 face image to 512-d emdding
    #input:
    #sess:tensorflow Session,with graph and parm load from MTCNN and Facenet model
    #faces:python list ?*160*160*3,contain ? images
    #emd_list:python list, emddings of the faces in the database,load from json files
    #label_list:python list, labels of the labels in the database,contain the id(i.e. 171860692)of a person,load from json files
    #retrun:
    #act_list:python list,labels of deetcted and recognized people
        images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
        embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
        phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
        feed_dict = {images_placeholder: faces, phase_train_placeholder: False}
        emd_faces = sess.run(embeddings, feed_dict=feed_dict)
        emd_faces=np.array(emd_faces)
        emd_list=np.array(emd_list)
        com_arr=np.zeros([emd_faces.shape[0],emd_list.shape[0]])
        act_list=[]
        for i in range(len(emd_faces)):
            for j in range(len(emd_list)):
                com_arr[i][j]=np.sqrt(np.sum(np.square(np.subtract(emd_faces[i, :], emd_list[j, :]))))
        min_arg=np.argmin(com_arr,1)
        res_arr=com_arr[:,np.argmin(com_arr,1)]
        res_arr=res_arr.flatten()
        res_arr[res_arr>1]=-1
        for i in range(len(res_arr)):
            if(res_arr[i]>0):
                act_list.append(label_list[min_arg[i]])
        return act_list


def face_regcon(argpipe):
    global send_sig
    face_timer()
    send_list = []

    with tf.Graph().as_default() as graph:
        with tf.Session() as sess:
            emd_list, label_list = load_emddings()
            p_net, r_net, o_net = load_model(MODEL_PATH, sess)
            videoCapture = cv2.VideoCapture(0)
            success, frame = videoCapture.read()
            while success:
                if send_sig is True:
                    #print("sends")
                    if send_list:
                        argpipe.send(send_list)
                        send_list.clear()
                    else:
                        argpipe.send(-1)

                send_sig = False

                flag, faces = load_and_align_data(frame, 160, 44, p_net, r_net, o_net)
                if flag is True:
                    #print(faces.shape)
                    act_list = compare(sess, faces, emd_list, label_list)
                    for i in act_list:
                        if i not in send_list:
                            send_list.append(i)
                    #print(send_list)
                    # for i in act_list:
                    #     print(i)
                time.sleep(0.5)
                success, frame = videoCapture.read()



if __name__=="__main__":
    with tf.Graph().as_default() as graph:
        with tf.Session() as sess:
            ret_list=[]
            emd_list,label_list=load_emddings()
            p_net,r_net,o_net=load_model(MODEL_PATH,sess)
            videoCapture = cv2.VideoCapture(0)
            success, frame = videoCapture.read()
            while success :
                flag,faces=load_and_align_data(frame,160,44,p_net,r_net,o_net)
                if flag is True:
                    print(faces.shape)
                    act_list = compare(sess,faces,emd_list,label_list)

                    print(act_list)
                    # for i in act_list:
                    #     print(i)
                time.sleep(0.5)
                success, frame = videoCapture.read()

def face_timer():
    global send_sig
    if send_sig is False:
        send_sig = True
    timer = threading.Timer(4, face_timer)
    timer.start()
