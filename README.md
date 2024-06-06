# Azure Kinect For Python

Provides encapsulation of the Azure Kinect SDK for easy Python development

<!-- ![gif placeholder](image_url) -->

## Features

- Automatically register each device
- Multi-device support is provided
- Facilitate secondary development
- CUDA acceleration is available, see [Enable CUDA Acceleration](./docs/enable_cuda_acceleration.md)

## Prerequisite

In order to be able to use the library properly, you need to follow the two tutorials below to set up the Kinect Azure DK device properly

- [Set up your Azure Kinect DK](https://learn.microsoft.com/en-us/azure/kinect-dk/set-up-azure-kinect-dk)
- [Set up Body Tracking SDK](https://learn.microsoft.com/en-us/azure/kinect-dk/body-sdk-setup)

## Quick Installation

The library is not published to [Pypi](https://pypi.org/), so it can only be installed through the github repository address. However, you can still easily install the library with the following command:

```bash
pip install git+https://github.com/batu1579/azure-kinect-for-python.git
```

For a more detailed information, please see the [Installation Guide](./docs/installation_guide.md)

## Usage example

```python
import azure_kinect
```

## Changelog

See [CHANGELOG](./CHANGELOG.md)

## Contributing

Welcome to submit PR, issue and feature requests!
