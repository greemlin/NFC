FROM scottyhardy/docker-wine:latest

# Set up environment
ENV WINEARCH=win64
ENV WINEDEBUG=-all
ENV DISPLAY=:99
ENV PYTHONPATH="C:\Python38\Lib;C:\Python38\DLLs"
ENV WINEPATH="C:\Python38;C:\Python38\Scripts"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    libgl1-mesa-glx \
    libglib2.0-0 \
    python3-opencv \
    libopencv-dev \
    python3-pil \
    python3-pil.imagetk \
    && rm -rf /var/lib/apt/lists/*

# Initialize Wine
RUN wineboot -i && wineserver -w

# Download Python installer
RUN wget -O python.exe https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe

# Install Python (with retries)
RUN for i in 1 2 3; do \
        xvfb-run wine python.exe /quiet InstallAllUsers=1 PrependPath=1 && break || sleep 15; \
    done

# Clean up installer
RUN rm python.exe && wineserver -w

# Set working directory
WORKDIR /app

# Copy your application files
COPY . .

# Start Xvfb and install dependencies
RUN Xvfb :99 -screen 0 1024x768x16 & \
    sleep 5 && \
    DISPLAY=:99 wine cmd /c "C:\Python38\python.exe -m pip install --upgrade pip && \
    C:\Python38\Scripts\pip.exe install wheel && \
    C:\Python38\Scripts\pip.exe install -r requirements.txt && \
    C:\Python38\Scripts\pip.exe install pyinstaller && \
    C:\Python38\Scripts\pyinstaller.exe --clean --windowed build.spec"

# The executable will be in /app/dist/
