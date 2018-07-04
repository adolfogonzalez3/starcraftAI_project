
import argparse
LEARNING_RATE = 1e-4

def create_model_Atari(In, Out):
    from keras.layers import Input, Dense, Conv2D, Flatten, Reshape, BatchNormalization, Activation
    from keras.models import Model, load_model
    from keras.optimizers import RMSprop, Adam
    
    
    frame_inputs = Input(shape=In, name='Input')
    x = Conv2D(32, (8, 8), strides=(4,4), padding='same')(frame_inputs) # 16 by 16 by 4
    x = Activation('relu')(x)
    x = Conv2D(64, (4, 4), strides=(2,2), padding='same')(x) # 8 by 8 by 4
    x = Activation('relu')(x)
    x = Conv2D(64, (3, 3), strides=(1,1), padding='same')(x) # 8 by 8 by 4
    x = Activation('relu')(x)
    x = Flatten()(x)
    x = Dense(512, activation='relu')(x)
    x = Activation('relu')(x)
    Q_value_outputs = Dense(Out, activation='linear', name='Output')(x)
    model = Model(inputs=frame_inputs, outputs=Q_value_outputs)
    adam = Adam(lr=LEARNING_RATE)
    model.compile(optimizer=adam, loss='mse')
    return model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_shape', help='The input shape of the network ex. "--input_shape 80 80 4".',
                        type=int, nargs='+', default=[80, 80, 4])
    parser.add_argument('--output_shape', help='The output shape of the network ex. "--output_shape 2".',
                        type=int, default=2)
    parser.add_argument('--filename', help='The name of the file created', default='model.h5')
    args = parser.parse_args()
    model = create_model_Atari(args.input_shape, args.output_shape)
    model.save(args.filename)
    