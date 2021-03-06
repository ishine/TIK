# Copyright 2014-2016  Brno University of Technology (author: Karel Vesely)
#                2017  International Computer Science Institute (author: Hang Su)      

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
# WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
# MERCHANTABLITY OR NON-INFRINGEMENT.
# See the Apache 2 License for the specific language governing permissions and
# limitations under the License.

# Generated Nnet prototype

import math

def Glorot(dim1, dim2, with_glorot):
  if with_glorot:
    # 35.0 = magic number, gives ~1.0 in inner layers for hid-dim 1024dim,
    return 35.0 * math.sqrt(2.0/(dim1+dim2));
  else:
    return 1.0


def make_lstm_proto(feat_dim, output_dim, conf, nnet_proto_file):
  nnet_proto = open(nnet_proto_file, 'w')
  num_hid_layers = conf['num_hidden_layers']
  num_cells = conf['num_cells']
  lstm_type = conf['lstm_type']
  with_glorot = conf.get('with_glorot', True)
  use_peepholes = conf.get('use_peepholes', False)
  
  #Use batch normalization for affine transform
  batch_norm = conf.get('batch_norm', False)
  
  #Factor to rescale Normal distriburtion for initalizing weight matrices
  param_stddev_factor = conf.get('param_stddev_factor', 0.1)

  if batch_norm:
    affine_layer = 'BatchNormalization'
  else:
    affine_layer = 'AffineTransform'

  nnet_proto.write("<NnetProto>\n")
  num_proj_str = ""
  if 'num_proj' in conf:
    num_proj_str = "<NumProj> %d" % conf['num_proj']
  for i in range(num_hid_layers):
    nnet_proto.write("<%s> <NumCells> %d <UsePeepHoles> %s %s\n" % 
            (lstm_type, num_cells, use_peepholes, num_proj_str))
  
  lstm_out_dim = conf['num_proj'] if 'num_proj' in conf else num_cells
  nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f <LearnRateCoef> %f <BiasLearnRateCoef> %f\n" % \
      (affine_layer, lstm_out_dim, output_dim, 0.0, 0.0, \
       (param_stddev_factor * Glorot(num_cells, output_dim, with_glorot)), 1.0, 0.1))

  nnet_proto.write("</NnetProto>\n")
  nnet_proto.close()


def make_seq2class_proto(feat_dim, output_dim, conf, nnet_proto_file):
  nnet_proto = open(nnet_proto_file, 'w')
  num_hid_layers = conf['num_hidden_layers']
  num_hid_neurons = conf['hidden_units']
  num_pooling_neurons = conf.get('pooling_units', num_hid_neurons)
  with_glorot = conf.get('with_glorot', True)
  
  #Use batch normalization after nonlin
  batch_norm = conf.get('batch_norm', False)
  #Use batch norm before pooling layer?
  norm_before_pooling = conf.get('norm_before_pooling', True)

  #use batch normalization within affine transformation
  affine_batch_norm = conf.get('affine_batch_norm', False)
  
  #Factor to rescale Normal distriburtion for initalizing weight matrices
  param_stddev_factor = conf.get('param_stddev_factor', 0.1)

  #Add softmax layer at the end
  with_softmax = conf.get('with_softmax', True)

  if affine_batch_norm:
    affine_layer = 'AffineBatchNormalization'
  else:
    affine_layer = 'AffineTransform'

  hid_bias_mean = conf.get('hid_bias_mean', 0.0)

  #Set bias range for hidden activations (+/- 1/2 range around mean)
  hid_bias_range = conf.get('hid_bias_range', 0.1)

  nnet_proto.write("<NnetProto>\n")

  for i in range(num_hid_layers):
    layer_in_dim = feat_dim if (i == 0) else num_hid_neurons
    layer_out_dim = num_hid_neurons if (i != num_hid_layers-1) else num_pooling_neurons
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
      (affine_layer, layer_in_dim, layer_out_dim, hid_bias_mean, hid_bias_range, \
       (param_stddev_factor * Glorot(layer_in_dim, layer_out_dim, with_glorot))))
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], layer_out_dim, layer_out_dim))
    if batch_norm and norm_before_pooling and i != num_hid_layers - 1:
      nnet_proto.write("<BatchNormalization> <InputDim> %d <OutputDim> %d\n" % (layer_out_dim, layer_out_dim))
#    nnet_proto.write("<Dropout> keep_prob\n")

  if batch_norm:
    nnet_proto.write("<BatchNormalization> <InputDim> %d <OutputDim> %d\n" % (layer_out_dim, layer_out_dim))
  use_std = conf.get('use_std', False)
  layer_in_dim = layer_out_dim
  layer_out_dim = 2*layer_in_dim if use_std else layer_in_dim
  nnet_proto.write("<Pooling> <InputDim> %d <OutputDim> %d <UseStd> %s\n" % (layer_in_dim, layer_out_dim, use_std))

  embedding_layers = conf['embedding_layers']
  embedding_layer_units = [ int(i) for i in embedding_layers.split(':') ]

  for i in range(len(embedding_layer_units)):
    layer_in_dim = layer_out_dim if (i == 0) else embedding_layer_units[i-1]
    layer_out_dim = output_dim if (i == len(embedding_layer_units)) else embedding_layer_units[i]
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
      (affine_layer, layer_in_dim, layer_out_dim, hid_bias_mean, hid_bias_range, \
       (param_stddev_factor * Glorot(layer_in_dim, layer_out_dim, with_glorot))))
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], layer_out_dim, layer_out_dim))
    if batch_norm:
      nnet_proto.write("<BatchNormalization> <InputDim> %d <OutputDim> %d\n" % (layer_out_dim, layer_out_dim))
#    nnet_proto.write("<Dropout> keep_prob\n")

  nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
    (affine_layer, layer_out_dim, output_dim, 0.0, 0.0, \
     (param_stddev_factor * Glorot(layer_out_dim, output_dim, with_glorot))))
  
  # Optionaly append softmax
  if with_softmax:
    nnet_proto.write("<Softmax> <InputDim> %d <OutputDim> %d\n" % (output_dim, output_dim))

  nnet_proto.write("</NnetProto>\n")
  nnet_proto.close()


def make_nnet_proto(feat_dim, output_dim, conf, nnet_proto_file):

  nnet_proto = open(nnet_proto_file, 'w')
  num_hid_layers = conf['num_hidden_layers']
  num_hid_neurons = conf['hidden_units']
  num_hid_layers_after_bn = conf.get('num_hidden_layers_after_bn', 1)
  
  # Check
  assert(feat_dim > 0)
  assert(output_dim > 0)
  assert(num_hid_layers >= 0)
  assert(num_hid_neurons > 0)

  #Use batch normalization for affine transform
  batch_norm = conf.get('batch_norm', False)

  if batch_norm:
    affine_layer = 'BatchNormalization'
  else:
    affine_layer = 'AffineTransform'

  hid_bias_mean = conf.get('hid_bias_mean', -2.0)

  #Set bias range for hidden activations (+/- 1/2 range around mean)
  hid_bias_range = conf.get('hid_bias_range', 4.0)

  #Factor to rescale Normal distriburtion for initalizing weight matrices
  param_stddev_factor = conf.get('param_stddev_factor', 0.1)

  #Generate normalized weights according to X.Glorot paper, but mapping U->N with same variance (factor sqrt(x/(dim_in+dim_out)))'
  with_glorot = conf.get('with_glorot', True)

  #1/12 reduction of stddef in input layer [default: %default]
  smaller_input_weights = conf.get('smaller_input_weights', False)

  #Smaller initial weights and learning rate around bottleneck
  bottleneck_trick = conf.get('bottleneck_trick', True)

  #Make bottleneck network with desired bn-dim (0 = no bottleneck)
  bottleneck_dim = conf.get('bottleneck_dim', 0)

  #Add softmax layer at the end
  with_softmax = conf.get('with_softmax', True)
  
  #Or add softmax layer at the end
  with_nonlin = conf.get('with_nonlin', True)

  #Use batch normalization for affine transform
  batch_norm = conf.get('batch_norm', False)

  if batch_norm:
    affine_layer = 'BatchNormalization'
  else:
    affine_layer = 'AffineTransform'

  nnet_proto.write("<NnetProto>\n")

  # Begin the prototype,
  # First AffineTranform,
  nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
    (affine_layer, feat_dim, num_hid_neurons, hid_bias_mean, hid_bias_range, \
     (param_stddev_factor * Glorot(feat_dim, num_hid_neurons, with_glorot) * \
      (math.sqrt(1.0/12.0) if smaller_input_weights else 1.0))))
    # Note.: compensating dynamic range mismatch between input features and Sigmoid-hidden layers,
    # i.e. mapping the std-dev of N(0,1) (input features) to std-dev of U[0,1] (sigmoid-outputs).
    # This is done by multiplying with stddev(U[0,1]) = sqrt(1/12).
    # The stddev of weights is consequently reduced with scale 0.29,
  nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], num_hid_neurons, num_hid_neurons))

  # Internal AffineTransforms,
  for i in range(num_hid_layers-1):
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
          (affine_layer, num_hid_neurons, num_hid_neurons, hid_bias_mean, hid_bias_range, \
           (param_stddev_factor * Glorot(num_hid_neurons, num_hid_neurons, with_glorot))))
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], num_hid_neurons, num_hid_neurons))

  # Optionaly add bottleneck,
  if bottleneck_dim != 0:
    assert(bottleneck_dim > 0)
    nnet_proto.write("<BottleNeck>\n")
    if bottleneck_trick:
      # 25% smaller stddev -> small bottleneck range
      nnet_proto.write("<LinearTransform> <InputDim> %d <OutputDim> %d <ParamStddev> %f\n" % \
       (num_hid_neurons, bottleneck_dim, \
        (param_stddev_factor * Glorot(num_hid_neurons, bottleneck_dim, with_glorot) * 0.75 )))
      nnet_proto.write("</BottleNeck>\n")
      # 25% smaller stddev -> smaller gradient in prev. layer
      nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
       (affine_layer, bottleneck_dim, num_hid_neurons, hid_bias_mean, hid_bias_range, \
        (param_stddev_factor * Glorot(bottleneck_dim, num_hid_neurons, with_glorot) * 0.75 )))
    else:
      # Same learninig-rate and stddev-formula everywhere,
      nnet_proto.write("<LinearTransform> <InputDim> %d <OutputDim> %d <ParamStddev> %f\n" % \
       (num_hid_neurons, bottleneck_dim, \
        (param_stddev_factor * Glorot(num_hid_neurons, bottleneck_dim, with_glorot))))
      nnet_proto.write("</BottleNeck>\n")
      nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
       (affine_layer, bottleneck_dim, num_hid_neurons, hid_bias_mean, hid_bias_range, \
        (param_stddev_factor * Glorot(o.bottleneck_dim, num_hid_neurons, with_glorot))))
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], num_hid_neurons, num_hid_neurons))

    for i in range(num_hid_layers_after_bn-1):
      nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
            (affine_layer, num_hid_neurons, num_hid_neurons, hid_bias_mean, hid_bias_range, \
             (param_stddev_factor * Glorot(num_hid_neurons, num_hid_neurons, with_glorot))))
      nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], num_hid_neurons, num_hid_neurons))

  # Last AffineTransform
  nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
    (affine_layer, num_hid_neurons, output_dim, 0.0, 0.0, \
     (param_stddev_factor * Glorot(num_hid_neurons, output_dim, with_glorot))))

  # Optionaly append softmax
  if with_softmax:
    nnet_proto.write("<Softmax> <InputDim> %d <OutputDim> %d\n" % (output_dim, output_dim))
  
  if with_nonlin:
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], output_dim, output_dim))

  nnet_proto.write("</NnetProto>\n")
  nnet_proto.close()
  return output_dim


def make_asr_proto(input_dim, output_dim, conf, nnet_proto_file):

  nnet_proto = open(nnet_proto_file, 'w')
  num_hid_layers = conf['asr_hidden_layers']
  num_hid_neurons = conf['asr_hidden_units']
  
  # Check
  assert(input_dim > 0)
  assert(output_dim > 0)
  assert(num_hid_layers >= 0)
  assert(num_hid_neurons > 0)

  #Use batch normalization for affine transform
  batch_norm = conf.get('batch_norm', False)

  if batch_norm:
    affine_layer = 'BatchNormalization'
  else:
    affine_layer = 'AffineTransform'

  hid_bias_mean = conf.get('hid_bias_mean', -2.0)

  #Set bias range for hidden activations (+/- 1/2 range around mean)
  hid_bias_range = conf.get('hid_bias_range', 4.0)

  #Factor to rescale Normal distriburtion for initalizing weight matrices
  param_stddev_factor = conf.get('param_stddev_factor', 0.1)

  #Generate normalized weights according to X.Glorot paper, but mapping U->N with same variance (factor sqrt(x/(dim_in+dim_out)))'
  with_glorot = conf.get('with_glorot', True)

  #Add softmax layer at the end
  with_softmax = conf.get('with_softmax', True)

  #Use batch normalization for affine transform
  batch_norm = conf.get('batch_norm', False)

  if batch_norm:
    affine_layer = 'BatchNormalization'
  else:
    affine_layer = 'AffineTransform'

  nnet_proto.write("<NnetProto>\n")

  # Internal AffineTransforms,
  num_hid_input = input_dim
  for i in range(num_hid_layers):
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
          (affine_layer, num_hid_input, num_hid_neurons, hid_bias_mean, hid_bias_range, \
           (param_stddev_factor * Glorot(num_hid_neurons, num_hid_neurons, with_glorot))))
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], num_hid_neurons, num_hid_neurons))
    num_hid_input = num_hid_neurons

  # Last AffineTransform
  nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
    (affine_layer, num_hid_neurons, output_dim, 0.0, 0.0, \
     (param_stddev_factor * Glorot(num_hid_neurons, output_dim, with_glorot))))

  # Optionaly append softmax
  if with_softmax:
    nnet_proto.write("<Softmax> <InputDim> %d <OutputDim> %d\n" % (output_dim, output_dim))
  
  nnet_proto.write("</NnetProto>\n")
  nnet_proto.close()


def make_sid_proto(input_dim, output_dim, conf, nnet_proto_file):
  nnet_proto = open(nnet_proto_file, 'w')
  num_hid_layers = conf['sid_hidden_layers']
  num_hid_neurons = conf['sid_hidden_units']
  num_pooling_neurons = conf.get('pooling_units', num_hid_neurons)
  with_glorot = conf.get('with_glorot', True)
  
  #Use batch normalization after nonlin
  batch_norm = conf.get('sid_batch_norm', False)

  #use batch normalization within affine transformation
  affine_batch_norm = conf.get('affine_batch_norm', False)
  
  #Factor to rescale Normal distriburtion for initalizing weight matrices
  param_stddev_factor = conf.get('param_stddev_factor', 0.1)

  #Add softmax layer at the end
  with_softmax = conf.get('with_softmax', True)

  if affine_batch_norm:
    affine_layer = 'AffineBatchNormalization'
  else:
    affine_layer = 'AffineTransform'

  hid_bias_mean = conf.get('hid_bias_mean', 0.0)

  #Set bias range for hidden activations (+/- 1/2 range around mean)
  hid_bias_range = conf.get('hid_bias_range', 0.1)

  nnet_proto.write("<NnetProto>\n")

  layer_out_dim = input_dim
  for i in range(num_hid_layers):
    layer_in_dim = input_dim if (i == 0) else num_hid_neurons
    layer_out_dim = num_hid_neurons if (i != num_hid_layers-1) else num_pooling_neurons
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
      (affine_layer, layer_in_dim, layer_out_dim, hid_bias_mean, hid_bias_range, \
       (param_stddev_factor * Glorot(layer_in_dim, layer_out_dim, with_glorot))))
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], layer_out_dim, layer_out_dim))
    if batch_norm:
      nnet_proto.write("<BatchNormalization> <InputDim> %d <OutputDim> %d\n" % (layer_out_dim, layer_out_dim))

  use_std = conf.get('use_std', False)
  layer_in_dim = layer_out_dim
  layer_out_dim = 2*layer_in_dim if use_std else layer_in_dim
  nnet_proto.write("<Pooling> <InputDim> %d <OutputDim> %d <UseStd> %s\n" % (layer_in_dim, layer_out_dim, use_std))

  embedding_layers = conf['embedding_layers']
  embedding_layer_units = [ int(i) for i in embedding_layers.split(':') ]

  for i in range(len(embedding_layer_units)):
    layer_in_dim = layer_out_dim if (i == 0) else embedding_layer_units[i-1]
    layer_out_dim = output_dim if (i == len(embedding_layer_units)) else embedding_layer_units[i]
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
      (affine_layer, layer_in_dim, layer_out_dim, hid_bias_mean, hid_bias_range, \
       (param_stddev_factor * Glorot(layer_in_dim, layer_out_dim, with_glorot))))
    nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d\n" % (conf['nonlin'], layer_out_dim, layer_out_dim))
    if batch_norm:
      nnet_proto.write("<BatchNormalization> <InputDim> %d <OutputDim> %d\n" % (layer_out_dim, layer_out_dim))

  nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
    (affine_layer, layer_out_dim, output_dim, 0.0, 0.0, \
     (param_stddev_factor * Glorot(layer_out_dim, output_dim, with_glorot))))
  
  # Optionaly append softmax
  if with_softmax:
    nnet_proto.write("<Softmax> <InputDim> %d <OutputDim> %d\n" % (output_dim, output_dim))

  nnet_proto.write("</NnetProto>\n")
  nnet_proto.close()


def sid_append_top(conf, output_dim, nnet_proto_file):
  nnet_proto = open(nnet_proto_file, 'w')
  with_glorot = conf.get('with_glorot', True)
  
  #use batch normalization within affine transformation
  affine_batch_norm = conf.get('affine_batch_norm', False)

  if affine_batch_norm:
    affine_layer = 'AffineBatchNormalization'
  else:
    affine_layer = 'AffineTransform'

  embedding_layers = conf['embedding_layers']
  embedding_layer_units = [ int(i) for i in embedding_layers.split(':') ]
 
  hid_bias_mean = conf.get('hid_bias_mean', 0.0)
  hid_bias_range = conf.get('hid_bias_range', 0.1)
  param_stddev_factor = conf.get('param_stddev_factor', 0.1)

  nnet_proto.write("<NnetProto>\n")

  layer_in_dim = embedding_layer_units[-1]
  layer_out_dim = output_dim

  nnet_proto.write("<%s> <InputDim> %d <OutputDim> %d <BiasMean> %f <BiasRange> %f <ParamStddev> %f\n" % \
      (affine_layer, layer_in_dim, layer_out_dim, hid_bias_mean, hid_bias_range, \
       (param_stddev_factor * Glorot(layer_in_dim, layer_out_dim, with_glorot))))

  nnet_proto.write("</NnetProto>\n")
  nnet_proto.close()
