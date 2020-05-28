from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt
from model import MobileNetV2
import tensorflow as tf
import json
import os
import math
import numpy as np
from prettytable import PrettyTable


class ConfusionMatrix(object):
    """
    注意，如果显示的图像不全，是matplotlib版本问题
    本例程使用matplotlib-3.2.1(windows and ubuntu)绘制正常
    """
    def __init__(self, num_classes: int, labels: list):
        self.matrix = np.zeros((num_classes, num_classes))
        self.num_classes = num_classes
        self.labels = labels

    def update(self, preds, labels):
        for p, t in zip(preds, labels):
            self.matrix[p, t] += 1

    def summary(self):
        # calculate accuracy
        sum_TP = 0
        for i in range(self.num_classes):
            sum_TP += self.matrix[i, i]
        acc = sum_TP / np.sum(self.matrix)
        print("the model accuracy is ", acc)

        # precision, recall, specificity
        table = PrettyTable()
        table.field_names = ["", "Precision", "Recall", "Specificity"]
        for i in range(self.num_classes):
            TP = self.matrix[i, i]
            FP = np.sum(self.matrix[:, i]) - TP
            FN = np.sum(self.matrix[i, :]) - TP
            TN = np.sum(self.matrix) - TP - FP - FN
            Precision = round(TP / (TP + FP), 3)
            Recall = round(TP / (TP + FN), 3)
            Specificity = round(TN / (TN + FP), 3)
            table.add_row([self.labels[i], Precision, Recall, Specificity])
        print(table)

    def plot(self):
        matrix = self.matrix
        print(matrix)
        plt.imshow(matrix, cmap=plt.cm.Blues)

        # 设置x轴坐标label
        plt.xticks(range(self.num_classes), self.labels, rotation=45)
        # 设置y轴坐标label
        plt.yticks(range(self.num_classes), self.labels)
        # 显示colorbar
        plt.colorbar()
        plt.xlabel('True Labels')
        plt.ylabel('Predicted Labels')
        plt.title('Confusion matrix')

        # 在图中标注数量/概率信息
        thresh = matrix.max() / 2
        for x in range(self.num_classes):
            for y in range(self.num_classes):
                # 注意这里的matrix[y, x]不是matrix[x, y]
                info = int(matrix[y, x])
                plt.text(x, y, info,
                         verticalalignment='center',
                         horizontalalignment='center',
                         color="white" if info > thresh else "black")
        plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    data_root = os.path.abspath(os.path.join(os.getcwd(), "../.."))  # get data root path
    image_path = data_root + "/data_set/flower_data/"  # flower data set path
    train_dir = image_path + "train"
    validation_dir = image_path + "val"

    im_height = 224
    im_width = 224
    batch_size = 16


    def pre_function(img):
        # img = im.open('test.jpg')
        # img = np.array(img).astype(np.float32)
        img = img / 255.
        img = (img - 0.5) * 2.0
        return img


    # data generator with data augmentation
    validation_image_generator = ImageDataGenerator(preprocessing_function=pre_function)

    val_data_gen = validation_image_generator.flow_from_directory(directory=validation_dir,
                                                                  batch_size=batch_size,
                                                                  shuffle=False,
                                                                  target_size=(im_height, im_width),
                                                                  class_mode='categorical')
    # img, _ = next(train_data_gen)
    total_val = val_data_gen.n

    model = MobileNetV2(num_classes=5)
    # feature.build((None, 224, 224, 3))  # when using subclass model
    model.load_weights('myMobileNet.ckpt')

    # read class_indict
    try:
        json_file = open('./class_indices.json', 'r')
        class_indict = json.load(json_file)
    except Exception as e:
        print(e)
        exit(-1)

    labels = [label for _, label in class_indict.items()]
    confusion = ConfusionMatrix(num_classes=5, labels=labels)

    # validate
    for step in range(math.ceil(total_val / batch_size)):
        val_images, val_labels = next(val_data_gen)
        results = model.predict_on_batch(val_images)
        results = tf.keras.layers.Softmax()(results).numpy()
        results = np.argmax(results, axis=-1)
        labels = np.argmax(val_labels, axis=-1)
        confusion.update(results, labels)
    confusion.plot()
    confusion.summary()
