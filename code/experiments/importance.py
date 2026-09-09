"""E1 attribute-importance methods. Each returns a score vector (higher = more
important), computed on TRAINING data only (leakage-free).

Methods:
  pai       - Persistence-based Attribute Importance (this paper): leave-one-out
              bottleneck distance summed over H0..H_maxdim.
  nrs       - Neighborhood rough-set significance: drop in positive region
              (k-NN label consistency) when attribute removed. Label-local.
  relieff   - ReliefF (skrebate).
  mutual_info - Mutual information with label (sklearn).
  variance  - Per-feature variance (on standardized data ~ all 1, so this is a
              near-null baseline; kept to show PAI != scale/variance).
"""
import warnings
import numpy as np
from scipy.spatial.distance import pdist, squareform
from ripser import ripser
from persim import bottleneck
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_selection import mutual_info_classif

warnings.filterwarnings("ignore")

DEFAULT_MAXDIM = 1
DEFAULT_THRESH = 2.0


def pai_scores(X, y=None, maxdim=DEFAULT_MAXDIM, thresh=DEFAULT_THRESH):
    """Leave-one-out bottleneck distance. y ignored (label-free)."""
    dgm_full = ripser(X, maxdim=maxdim, thresh=thresh)["dgms"]
    d = X.shape[1]
    scores = np.zeros(d)
    for j in range(d):
        Xd = np.delete(X, j, axis=1)
        dgm_d = ripser(Xd, maxdim=maxdim, thresh=thresh)["dgms"]
        scores[j] = sum(bottleneck(dgm_full[k], dgm_d[k]) for k in range(maxdim + 1))
    return scores


def _positive_region(X, y, k=7):
    n = X.shape[0]
    kk = min(k + 1, n)
    nn = NearestNeighbors(n_neighbors=kk).fit(X)
    _, idx = nn.kneighbors(X)
    return np.mean([np.all(y[idx[i, 1:]] == y[i]) for i in range(n)])


def nrs_scores(X, y, k=7):
    """Significance = gamma(full) - gamma(without j). Label-local."""
    d = X.shape[1]
    if d == 1:
        return np.array([_positive_region(X, y, k)])
    gamma_full = _positive_region(X, y, k)
    scores = np.zeros(d)
    for j in range(d):
        Xd = np.delete(X, j, axis=1)
        scores[j] = gamma_full - _positive_region(Xd, y, k)
    return scores


def relieff_scores(X, y):
    from skrebate import ReliefF
    n_neighbors = min(10, X.shape[0] - 1)
    rf = ReliefF(n_neighbors=n_neighbors)
    rf.fit(X, y)
    return np.asarray(rf.feature_importances_, dtype=float)


def mutual_info_scores(X, y):
    return mutual_info_classif(X, y, random_state=0)


def variance_scores(X, y=None):
    return X.var(axis=0)


METHODS = {
    "pai": pai_scores,
    "nrs": nrs_scores,
    "relieff": relieff_scores,
    "mutual_info": mutual_info_scores,
    "variance": variance_scores,
}

# label-free methods (do not use y) -- for documentation/audit
LABEL_FREE = {"pai", "variance"}
