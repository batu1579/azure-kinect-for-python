from typing import Optional

import cv2
import cv2.typing as cvt
import numpy as np
import open3d as o3d

from azure_kinect.k4a.image_wrapper import K4AImage


class PointCloud(K4AImage):
    def to_numpy(self) -> cvt.MatLike | None:
        cloud_array = super().to_numpy()

        return None if cloud_array is None else cloud_array.reshape((-1, 3))

    def to_o3d_point_cloud(
        self,
        color_image_array: Optional[cvt.MatLike] = None,
    ) -> o3d.geometry.PointCloud | None:
        """Converts the point cloud to an Open3D point cloud object.

        Args:
            color_image_array (Optional[cvt.MatLike]): An optional color image
                array to add color to the point cloud. If provided, it should
                have the same width and height as the depth image used to
                create the point cloud.

        Returns:
            o3d.geometry.PointCloud | None: An Open3D point cloud object, or
                None if the conversion failed.
        """
        cloud_array = self.to_numpy()

        if cloud_array is None:
            return None

        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(cloud_array)

        if color_image_array is not None:
            colors = (
                cv2.cvtColor(
                    color_image_array,
                    cv2.COLOR_BGRA2RGB,
                )
                .reshape(-1, 3)
                .astype(np.float64)
                / 255
            )
            cloud.colors = o3d.utility.Vector3dVector(colors)

            cloud.transform(
                [
                    [1, 0, 0, 0],
                    [0, -1, 0, 0],
                    [0, 0, -1, 0],
                    [0, 0, 0, 1],
                ]
            )

        return cloud
