"""
Created by Dannier Li (Chlerry) between Mar 30 and June 25 in 2020 
"""
# Disable INFO and WARNING messages from TensorFlow
import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='1'

import keras
from utility.parameter import *
from utility.helper import psnr, load_imgs, regroup, save_imgs, performance_evaluation, image_to_block
import coarse.test
from prediction.b1_inference import pred_inference_b1

# =================================================
# Limit GPU memory(VRAM) usage in TensorFlow 2.0
# https://github.com/tensorflow/tensorflow/issues/34355
# https://medium.com/@starriet87/tensorflow-2-0-wanna-limit-gpu-memory-10ad474e2528
import tensorflow as tf
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)
# =================================================
import keras.backend as K
if rtx_optimizer == True:
    K.set_epsilon(1e-4) 
# =================================================

def pred_inference_b23(prev_decoded, predicted_b1_frame, b, bm, ratio, model = "prediction"):
    
    N_frames = prev_decoded.shape[0]
    # =================================================
    prev = image_to_block(prev_decoded, b, True)
    
    B = image_to_block(predicted_b1_frame, b, True)
    # =================================================
    json_path, hdf5_path = get_model_path(model, ratio)
    
    from keras.models import model_from_json
    json_file = open(json_path, 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    pred_model = model_from_json(loaded_model_json)
    # Load weights into new model
    pred_model.load_weights(hdf5_path)
    print("Loaded model from " + hdf5_path)
    
    # =================================================
    # Evaluate loaded model on test data
    opt = tf.keras.optimizers.Adam()
    if rtx_optimizer == True:
        opt = tf.train.experimental.enable_mixed_precision_graph_rewrite(opt)
    pred_model.compile(optimizer=opt, loss=keras.losses.MeanAbsoluteError(), metrics=['acc'])

    predicted_b23 = pred_model.predict([prev, B])

    predicted_b23_frame = regroup(N_frames, prev_decoded.shape, predicted_b23, bm)
    return predicted_b23_frame
    # ===================================================
    
def main(args = 1): 
    
    b = 16 
    bm = 8 
    
    test_images =  load_imgs(data_dir, test_start, test_end)
    decoded = coarse.test.predict(test_images, b, testing_ratio)

    predicted_b1_frame = pred_inference_b1(decoded, b, bm, testing_ratio)
    from residue.b_inference import residue_inference
    final_predicted_b1 = residue_inference(test_images[2:-2], predicted_b1_frame, b, testing_ratio, "residue_b1")

    predicted_b2_frame = pred_inference_b23(decoded[:-4], final_predicted_b1, b, bm, testing_ratio)
    print(decoded[:-4].shape)
    print(final_predicted_b1.shape)
    print(predicted_b2_frame.shape)

    n_predicted2, amse2, apsnr2, assim2 \
        = performance_evaluation(test_images[1:-3], predicted_b2_frame, 0, 1)
    print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
    print('n_b2:',n_predicted2)
    print('average test b2_amse:',amse2)
    print('average test b2_apsnr:',apsnr2)
    print('average test b2_assim:',assim2)

if __name__ == "__main__":   
    import sys
    main(sys.argv[1:])