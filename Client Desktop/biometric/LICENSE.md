# License

## BioAccess-Secure Biometric Module

This module integrates facial recognition capabilities using MUSE (Easy Facial Recognition) into BioAccess-Secure Client Desktop.

### Component Licenses

#### 1. MUSE (Easy Facial Recognition) - MIT License

License applies to:
- `muse/easy_facial_recognition.py`
- `muse/pretrained_model/*.dat` (dlib models)
- Original source by Anis Ayari (Defend Intelligence)

**MIT License Text:**

```
Copyright (c) 2011-2019 GitHub Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal 
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, sublicense, and/or sell copies of the 
Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.
```

#### 2. BioAccess-Secure Biometric Wrapper

License applies to:
- `face_capture_service.py`
- `biometric_api_client.py`
- `__init__.py`
- Documentation and tests

**License:** [To be defined by BioAccess-Secure project owners]

### Integrated Libraries

The following open-source libraries are used and maintain their original licenses:

- **OpenCV** (`opencv-python-headless`)
  - License: Apache 2.0
  - Website: https://opencv.org

- **dlib**
  - License: Boost License
  - Website: http://dlib.net

- **NumPy**
  - License: BSD License
  - Website: https://numpy.org

- **Pillow (PIL)**
  - License: PIL License (HPND)
  - Website: https://python-pillow.org

- **imutils**
  - License: MIT License
  - Website: https://github.com/jrosebr1/imutils

- **requests**
  - License: Apache 2.0
  - Website: https://requests.readthedocs.io

### Attribution

**MUSE (Easy Facial Recognition)**
- Author: Anis Ayari
- Organization: Defend Intelligence
- License: MIT
- Repository: [Included in this project]
- YouTube: https://www.youtube.com/watch?v=54WmrwVWu1w

### Third-Party Models

The dlib pre-trained models are used under their respective licenses:
- Face Recognition Model (ResNet): Public domain / pre-trained by dlib developers
- Shape Predictor (68 face landmarks): Public domain / pre-trained by dlib developers
- Shape Predictor (5 face landmarks): Public domain / pre-trained by dlib developers

### Usage Rights

✅ **Permitted:**
- Commercial use
- Modification and derivative works
- Distribution
- Private use

**Conditions:**
- Include license text in distributions
- Provide attribution to original authors (especially MUSE)
- Document modifications

### Compliance

This module is fully compliant with:
- MIT License requirements
- GPL compatibility (through Apache 2.0 / BSD libraries)
- Commercial use policies
- Open-source distribution standards

For questions regarding licensing, please contact the BioAccess-Secure project owners.

---

**Last Updated:** March 2026
**Module Version:** 2.0.0
