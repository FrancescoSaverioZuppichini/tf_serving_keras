'''
Send JPEG image to tensorflow_model_server loaded with GAN model.

Hint: the code has been compiled together with TensorFlow serving
and not locally. The client is called in the TensorFlow Docker container
'''

import time

from argparse import ArgumentParser

# Communication to TensorFlow server via gRPC
from grpc.beta import implementations
import tensorflow as tf

# TensorFlow serving stuff to send messages
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2
from tensorflow.contrib.util import make_tensor_proto

from tensorflow.contrib.util import make_tensor_proto

from os import listdir
from os.path import isfile, join


def parse_args():
    parser = ArgumentParser(description='Request a TensorFlow server for a prediction on the image')
    parser.add_argument('-s', '--server',
                        dest='server',
                        default='172.17.0.2:9000',
                        help='prediction service host:port')
    parser.add_argument('-i', '--image_path',
                        dest='image_path',
                        default='',
                        help='path to images folder',)
    parser.add_argument('-b', '--batch_mode',
                        dest='batch_mode',
                        default='true',
                        help='send image as batch or one-by-one')
    args = parser.parse_args()

    host, port = args.server.split(':')
    
    return host, port, args.image_path, args.batch_mode == 'true'


def main():
    # parse command line arguments
    host, port, image_path, batch_mode = parse_args()

    channel = implementations.insecure_channel(host, int(port))
    stub = prediction_service_pb2.beta_create_PredictionService_stub(channel)

    filenames = [(image_path + '/' + f) for f in listdir(image_path) if isfile(join(image_path, f))]
    files = []
    imagedata = []
    for filename in filenames:
        f = open(filename, 'rb')
        files.append(f)

        data = f.read()
        imagedata.append(data)

    start = time.time()

    if batch_mode:
        print('In batch mode')
        request = predict_pb2.PredictRequest()
        request.model_spec.name = 'dog_breed'
        request.model_spec.signature_name = 'serving_default'

        request.inputs['examples'].CopyFrom(make_tensor_proto(imagedata, shape=[len(imagedata)]))

        result = stub.Predict(request, 60.0)
        print(result)
    else:
        print('In one-by-one mode')
        for data in imagedata:
            request = predict_pb2.PredictRequest()
            request.model_spec.name = 'dog_breed'
            request.model_spec.signature_name = 'serving_default'

            request.inputs['examples'].CopyFrom(make_tensor_proto(data, shape=[1]))
            
            result = stub.Predict(request, 60.0)  # 60 secs timeout
            print(result)

    end = time.time()
    time_diff = end - start
    print('time elapased: {}'.format(time_diff))


if __name__ == '__main__':
    main()
