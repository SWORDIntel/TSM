import os
import sys
from grpc_tools import protoc

# The path to the proto file
proto_file = "mobile/android/app/src/main/proto/TSMService.proto"

# The output directories
python_out = "mock_server/"
java_out = "mobile/android/app/src/main/java/"

# The include path
include_path = "mobile/android/app/src/main/proto"

# The command to run
command = [
    "grpc_tools.protoc",
    f"--proto_path={include_path}",
    f"--python_out={python_out}",
    f"--grpc_python_out={python_out}",
    proto_file,
]

command = [
    "grpc_tools.protoc",
    f"--proto_path={include_path}",
    f"--python_out={python_out}",
    f"--grpc_python_out={python_out}",
    proto_file,
]

# Run the command
exit_code = protoc.main(command)

if exit_code != 0:
    print(f"Error compiling proto file: {exit_code}")
    sys.exit(exit_code)
