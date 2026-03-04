#!/usr/bin/env python
"""Script simples para rodar a app - sem emojis, sem problemas"""
import os
import sys

os.environ['PYTHONUNBUFFERED'] = '1'

if __name__ == '__main__':
    from app import app
    app.run(debug=False, host='0.0.0.0', port=5000)
