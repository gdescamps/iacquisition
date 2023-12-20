import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster


def compute_classification_hierarchical(data, min, max, plot=False):
    array = np.array(list(data.values())).reshape(-1, 1)

    # Calculate the range of the data
    data_range = max - min  # Peak to peak (max - min) of the data

    # Set the maximum distance threshold as a fraction of the range
    # This fraction can be adjusted based on the specific characteristics of your data
    threshold_fraction = 0.2  # For example, 20% of the range
    max_d = threshold_fraction * data_range

    # Hierarchical clustering
    Z = linkage(array, "ward")

    clusters = fcluster(Z, max_d, criterion="distance")
    if plot:
        #    Optional: Plotting the dendrogram for visualization
        plt.figure(figsize=(10, 7))
        dendrogram(Z)
        plt.title("Dendrogram for Hierarchical Clustering")
        plt.xlabel("Data Points")
        plt.ylabel("Euclidean distances")
        plt.axhline(y=max_d, color="r", linestyle="--")
        plt.show()

    return list(clusters)


def compute_smallest_boundingbox(columns_blocks_unique):
    res = []
    # Iterate through each column
    for __ in columns_blocks_unique:
        # Initialize min and max coordinates
        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")
        # Iterate through each bbox
        for box in __:
            (x1, y1), (x2, y2) = box
            min_x = np.min([min_x, x1, x2])
            min_y = np.min([min_y, y1, y2])
            max_x = np.max([max_x, x1, x2])
            max_y = np.max([max_y, y1, y2])

        # Smallest bounding box that contains all others
        smallest_bounding_box = ((min_x, min_y), (max_x, max_y))
        res.append(smallest_bounding_box)

        new_res = []

        for __ in res:
            new_res.append((tuple(__[0]), tuple(__[1])))

        unique_res = []
        for __ in set(new_res):
            unique_res.append(__)
    return unique_res


def remove_column_blocks_duplicate(columns_blocks):
    # Remove duplicates within each sublist
    unique_sublists = [list(set(sublist)) for sublist in columns_blocks]

    # Optional: Remove duplicate sublists
    # Convert each sublist to a tuple so they can be added to a set
    unique_sublists_as_tuples = set(tuple(sublist) for sublist in unique_sublists)

    # Convert back to a list of lists
    unique_list_of_lists = [list(sublist) for sublist in unique_sublists_as_tuples]

    return unique_list_of_lists


def block_segmentation(image_numpy, plot=False):
    gray_image = cv2.cvtColor(image_numpy, cv2.COLOR_BGR2GRAY)
    ret, thresh1 = cv2.threshold(
        gray_image, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV
    )
    rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 30))
    # Appplying dilation on the threshold image
    dilation = cv2.dilate(thresh1, rect_kernel, iterations=1)

    # Finding contours
    contours, hierarchy = cv2.findContours(
        dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    # Creating a copy of image
    im2 = gray_image.copy()
    # Looping through the identified contours
    # Then rectangular part is cropped and passed on
    # to pytesseract for extracting text from it
    # Extracted text is then written into the text file
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # Drawing a rectangle on copied image
        rect = cv2.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)
    if plot:
        plt.imshow(np.asarray(im2))
        plt.show()
    return contours


class SegmentationBlock:
    def __init__(self, x1, y1, x2, y2, id):
        self.x1 = x1  ## Left_To_Right axis. Top left point
        self.y1 = y1  ## Top_To_Bottom axis. Top left point
        self.x2 = x2  ## Left_To_Right axis. Bottom right point
        self.y2 = y2  ## Top_To_Bottom axis. Bottom right point
        self.id = id
        self.cluster = None
        # self.columns = []  ## List of all blocks on the same column

    def get_middle(self, axis):
        if axis == 1:
            return int((self.y2 - self.y1) / 2) + self.y1
        else:
            return int((self.x2 - self.x1) / 2) + self.x1

    def get_coordinates(self):
        return ((self.x1, self.y1), (self.x2, self.y2))

    def Isunder(self, block_to_compare):
        if self.y1 >= block_to_compare.y2:
            return True
        else:
            return False

    def Isnext(self, block_to_compare):
        if self.x1 >= block_to_compare.x2 or self.x2 <= block_to_compare.x1:
            return True
        elif self.x1 >= block_to_compare.x1 and self.x2 <= block_to_compare.x2:
            return False
        elif block_to_compare.x1 >= self.x1 and block_to_compare.x2 <= self.x2:
            return False
        elif self.x1 < block_to_compare.x1 and self.x2 > block_to_compare.x1:
            if self.x2 > block_to_compare.get_middle(axis=0):
                return False
            else:
                return True
        elif block_to_compare.x1 < self.x1 and block_to_compare.x2 > self.x1:
            if block_to_compare.x2 > self.get_middle(axis=0):
                return False
            else:
                return True

    def AssignClusterBlock(self, cluster_idx):
        self.cluster = cluster_idx


class DocumentBlocks:
    def __init__(self, contours, image_shape):
        self.blocks = []
        self.image_shape = image_shape
        for idx, cnt in enumerate(contours):
            x, y, w, h = cv2.boundingRect(cnt)
            self.blocks.append(
                SegmentationBlock(x1=x, y1=y, x2=x + w, y2=y + h, id=idx)
            )

    def get_block(self, id):
        return self.blocks[id]

    def get_blocks_coordinates_per_cluster(self, cluster_id):
        res = []
        for block_ in self.blocks:
            if block_.cluster == cluster_id:
                res.append(block_.get_coordinates())

        return res

    def return_list_to_remove(self):
        liste_id_to_remove = []
        image_area = self.image_shape[0] * self.image_shape[1]
        for _ in self.blocks:
            width = _.get_coordinates()[1][0] - _.get_coordinates()[0][0]
            height = _.get_coordinates()[1][1] - _.get_coordinates()[0][1]
            if width * height >= 0.98 * image_area:
                liste_id_to_remove.append(_.id)
            else:
                pass
            # self.blocks[key].remove_block()
        print(liste_id_to_remove)
        return liste_id_to_remove

    def remove_block(self, liste_id_to_remove):
        new_block_list = []
        for i, block in enumerate(self.blocks):
            if block.id in liste_id_to_remove:
                pass
            else:
                new_block_list.append(block)
        self.blocks = new_block_list
        return None
