import fire # https://github.com/google/python-fire/blob/master/docs/guide.md
import os

def up():
  command = 'docker compose -f telegram/docker-compose.yaml  up --build --detach'
  os.system(command)

def down():
  command = 'docker compose -f telegram/docker-compose.yaml  down --rmi all --volumes --remove-orphans'
  os.system(command)

if __name__ == '__main__':
  fire.Fire()