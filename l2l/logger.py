"""Log scalars and images to tensorboard without or without tensor ops
When logs are defined with tf.summary.<type> it is enough to call init
and add_summary, but also run merge all before. If you want to log
data without merge, you may only call init and log_<type>, which use
the tf.Summary() protocol buffer.
More info here: https://stackoverflow.com/questions/37902705/how-to-manually-create-a-tf-summary
"""
from io import StringIO
import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np


class Logger(object):
  """Logging in tensorboard without tensorflow ops."""

  def __init__(self, log_dir, graph=None):
    """Creates a summary writer logging to log_dir.
    :param: log_dir: system path to logs
    :param graph: session graph to print to file
    """
    self.writer = tf.summary.FileWriter(log_dir, graph)

  def add_summary(self, summary, step):
    """Adds a summary to the current writer
    :param summary: tf summary object
    :param step: training iteration
    """
    self.writer.add_summary(summary, step)
    self.flush()

  def flush(self):
    """Wrapper for writer flush
    """
    self.writer.flush()

  def log_scalar(self, tag, value, step):
    """Log a scalar variable.
    :param tag: name of the scalar
    :param value: value of the scalar
    :param step: training iteration
    """
    summary = tf.Summary(value=[tf.Summary.Value(tag=tag,
                                                 simple_value=value)])
    self.writer.add_summary(summary, step)
    self.flush()

  def log_images(self, tag, images, step):
    """Logs a list of images.
    :param tag: name of the histogram
    :param images: a list of images to log
    :param step: training iteration
    """
    im_summaries = []
    for nr, img in enumerate(images):
      # Write the image to a string
      s = StringIO()
      plt.imsave(s, img, format='png')

      # Create an Image object
      img_sum = tf.Summary.Image(encoded_image_string=s.getvalue(),
                                 height=img.shape[0],
                                 width=img.shape[1])
      # Create a Summary value
      im_summaries.append(tf.Summary.Value(tag='%s/%d' % (tag, nr),
                                           image=img_sum))

    # Create and write Summary
    summary = tf.Summary(value=im_summaries)
    self.writer.add_summary(summary, step)

  def log_histogram(self, tag, values, step, bins=1000):
    """Logs the histogram of a list/vector of values.
    :param tag:
    :param values:
    :param step:
    """
    # Convert to a numpy array
    values = np.array(values)

    # Create histogram using numpy
    counts, bin_edges = np.histogram(values, bins=bins)

    # Fill fields of histogram proto
    hist = tf.HistogramProto()
    hist.min = float(np.min(values))
    hist.max = float(np.max(values))
    hist.num = int(np.prod(values.shape))
    hist.sum = float(np.sum(values))
    hist.sum_squares = float(np.sum(values**2))

    # Requires equal number as bins, where the first goes from -DBL_MAX to bin_edges[1]
    # See https://github.com/tensorflow/tensorflow/blob/master/tensorflow/core/framework/summary.proto#L30
    # Thus, we drop the start of the first bin
    bin_edges = bin_edges[1:]

    # Add bin edges and counts
    for edge in bin_edges:
      hist.bucket_limit.append(edge)
    for c in counts:
      hist.bucket.append(c)

    # Create and write Summary
    summary = tf.Summary(value=[tf.Summary.Value(tag=tag, histo=hist)])
    self.writer.add_summary(summary, step)
    self.flush()
