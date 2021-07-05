start-dnb-for-data-hub-api:
	[ -z "$(shell docker network ls --filter=name=dh_default -q)" ] && docker network create dh_default || echo 'dh_default network already present'
	docker-compose -p dnb-service -f ../dnb-service/docker-compose.data-hub-api.yml up &

stop-dnb-for-data-hub-api:
	docker-compose -p dnb-service -f ../dnb-service/docker-compose.data-hub-api.yml down
