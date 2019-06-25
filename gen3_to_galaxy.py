from bioblend.galaxy import GalaxyInstance
import argparse

# get arguments
parser = argparse.ArgumentParser()

parser.add_argument("-a", "--api-key")
parser.add_argument("-s", "--server-address")
parser.add_argument("-p", "--port", default=80)
parser.add_argument("-m", )

parser.parse_args()
