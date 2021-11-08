start-dnb-for-data-hub-api:
	[ -z "$(shell docker network ls --filter=name=data-infrastructure-shared-network -q)" ] && docker network create data-infrastructure-shared-network || echo 'data-infrastructure-shared-network network already present'
	docker-compose -p dnb-service -f ../dnb-service/docker-compose.data-hub-api.yml up &

stop-dnb-for-data-hub-api:
	docker-compose -p dnb-service -f ../dnb-service/docker-compose.data-hub-api.yml down
