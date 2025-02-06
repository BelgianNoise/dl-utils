# dl-downer

A simple low-level python script that downloads file from the internet.

## Usage

### Server

These scripts offer the possiblity to monitor a database and wait for new download request and download them when available.
To run this on a server as a database monitor, it is recommended you run the docker container for which the Dockerfile is provided.
Alternatively, you can run the `start.py` script.

### CLI

You can also run this script from your terminal, this requires a little more setup though.

#### prerequisites
 - Have python installed
 - Have pip installed

#### Steps
1. Run `pip install --no-cache-dir -r requirements.txt` to install the required packages
2. Run `playwright install`
3. Add all binaries to your PATH and make sure they are globally accessible. Find your binaries in `./binaries/windows`
4. Test the binaries using `n-m3u8dl-re.exe -h`
5. Set the required variables in `cli.py` (login credentials, ...)
6. Run `python cli.py <video_url>`
