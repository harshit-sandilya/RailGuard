port=$(yq '.server.kafka-port' config.yaml)
host=$(yq '.server.host' config.yaml)
UNITY_PATH=$(which unity-editor || which unity)

kafka-topics --create --topic route --bootstrap-server $host:$port --partitions 3 --replication-factor 1
python -m router.main
# kafka-topics --create --topic control --bootstrap-server $host:$port --partitions 3 --replication-factor 1 --config cleanup.policy=compact
# kafka-topics --create --topic data --bootstrap-server $host:$port --partitions 3 --replication-factor 1
# if [ -n "$UNITY_PATH" ]; then
#     "$UNITY_PATH" -projectPath /Users/harshit/Projects/RailGuard/environment
# else
#     echo "Unity not found on the system."
#     exit 1
# fi

kafka-topics --delete --topic route --bootstrap-server $host:$port
# kafka-topics --delete --topic control --bootstrap-server $host:$port
# kafka-topics --delete --topic data --bootstrap-server $host:$port
