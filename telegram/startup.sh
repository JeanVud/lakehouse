docker compose -f telegram/docker-compose.yaml  up --build
# Uncomment the line below to run in detached mode
# docker compose -f telegram/docker-compose.yaml  up --build --detach 


# Uncomment the line below to stop and remove containers, networks, images, and volumes
# docker compose -f telegram/docker-compose.yaml  down --rmi all --volumes --remove-orphans