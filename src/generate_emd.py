#thie file is used to generated emddings of faces from raw pictures

import tensorflow as tf
import numpy as np
import os
import align.detect_face
from tensorflow.python.platform import gfile
import cv2
import json
import video
SRC_DIR=r'./imgdata/comm_160'
DEST_DIR=r'./proj/face_emddings'
MODEL_PATH=r'./model/20180402-114759/20180402-114759.pb'
def load_and_align_data(img, image_size, margin,p,r,o):
    minsize = 20  # minimum size of face
    threshold = [0.6, 0.7, 0.7]  # three steps's threshold
    factor = 0.709  # scale factor
    img_list = []
    img_size = np.asarray(img.shape)[0:2]
    bounding_boxes, _ = align.detect_face.detect_face(img, minsize, p, r, o, threshold, factor)
    if len(bounding_boxes) < 1:
        print("can't detect face, remove ")
        return -1,np.array([])
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
    return 1,images

def load_model(model, input_map=None):
    #load model from a tensorflow pb file
    model_exp = os.path.expanduser(model)
    print('Model filename: %s' % model_exp)
    with gfile.FastGFile(model_exp, 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, input_map=input_map, name='')
def read_images():
    #read raw images from SRC_DIR
    #images must have such name id(i.e. 171860692).png/.jpg
    #return
    #img_list:python list ,contain the images
    #label_list:python list,contain the labels
    img_list=[]
    label_list=[]
    for file_names in os.listdir(SRC_DIR):
        print(file_names)
        img=os.path.join(SRC_DIR,file_names)
        img=cv2.imread(img)
        img_list.append(img)
        label_list.append(file_names[:-4])
    return img_list,label_list
def prewhiten(x):
    #preprocess for a image
    #used in load and align data
    mean = np.mean(x)
    std = np.std(x)
    std_adj = np.maximum(std, 1.0 / np.sqrt(x.size))
    y = np.multiply(np.subtract(x, mean), 1 / std_adj)
    return y
def generate_emddings_json(img_list,label_list):
    #img_list:python list,contain the images you want to save
    #label_list:python list,contain the id correspanding to the images
    #return null
    #images will be saved in DEST_DIR with id as filename
    #all images will be saved in json format
    with tf.Graph().as_default():
        with tf.Session() as sess:
            # Load the model
            load_model(MODEL_PATH)
            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            # Run forward pass to calculate embeddings
            feed_dict = {images_placeholder: img_list, phase_train_placeholder: False}
            emb = sess.run(embeddings, feed_dict=feed_dict)
            emb=np.array(emb)
            emb = emb.tolist()
            for i in range(len(label_list)):
                with open(os.path.join(DEST_DIR, label_list[i] + ".emd"), "w") as f:
                    json.dump(emb[i], f)
                    print("successfully dump json file %s "%label_list[i])

if __name__=='__main__':
    with tf.Graph().as_default() as graph:
        with tf.Session() as sess:
            p_net, r_net, o_net = video.load_model(MODEL_PATH,sess)
            img_list,label_list=read_images()
            align_list=[]
            for i in img_list:
                flag, faces = video.load_and_align_data(i, 160, 44, p_net, r_net, o_net)
                if flag!=-1:
                    align_list.append(faces[0])
            generate_emddings_json(align_list,label_list)




