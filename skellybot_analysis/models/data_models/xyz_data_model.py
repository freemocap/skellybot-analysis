from typing import List

import numpy as np
from pydantic import BaseModel


class XYZData(BaseModel):
    x: float
    y: float
    z: float

    @property
    def as_np_array(self) -> np.ndarray:
        return np.array(self.as_list)

    @property
    def as_list(self) -> List[float]:
        return [self.x, self.y, self.z]

    @property
    def magnitude(self) -> float:
        return np.linalg.norm(self.as_np_array)

    @property
    def normalized(self) -> List[float]:
        return self.as_list / self.magnitude
