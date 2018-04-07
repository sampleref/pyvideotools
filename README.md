
1. To Build Docker Image:
    # cd /home/user
    # git clone https://github.com/sampleref/pyvideotools.git
    -- Skip below docker build to use existing image from nas2docker/py3ffmpeg3opencv3:stable
    # cd pyvideotools
    # docker build -t nas2docker/py3ffmpeg3opencv3:stable --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy .

2. Run Docker Image:
    # docker run -it -v /home/user:/home/user --net=host nas2docker/py3ffmpeg3opencv3:stable

3. Inside docker container run scripts using:
    # python /home/user/pyvideotools/App.py