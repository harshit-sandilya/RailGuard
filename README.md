# RailGuard

A railway traffic management and collision prevention system that uses reinforcement learning to optimize train routing and prevent collisions.

## Project Overview

RailGuard is a digital twin simulation environment for railway systems that enables:
- Real-time train tracking and management
- Collision detection and prevention
- Route optimization using reinforcement learning
- Simulation of complex railway networks

## Setup and Installation

### Prerequisites

- Python 3.9+
- Unity (for the digital twin simulation)
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/harshit-sandilya/RailGuard.git
cd RailGuard
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root directory with the following content:
```
UNITY_PATH=/path/to/unity/executable
```
Replace `/path/to/unity/executable` with your actual Unity installation path.

## Project Structure

- `controller/`: Contains the controller components for managing train communication
- `router/`: Handles routing and communication between components
- `schema/`: Contains data schema definitions
- `utils/`: Utility functions for the project
- `logs/`: Directory where simulation logs and training results are stored
- `simulate.py`: Script to run simulations
- `train.py`: Script to train the reinforcement learning model

## Configuration

The project uses a configuration file (`config.yaml`) to set various parameters for the simulation environment. You can customize:

- Train physical properties (length, mass, speed, etc.)
- Station dimensions
- Physics simulation parameters
- Time scaling factors
- Control parameters

## Running the System

### Simulation Mode

To run a simulation and generate a collision report:

```bash
python simulate.py --trains <number_of_trains> --stations <number_of_stations> --port <port_number>
```

Arguments:
- `--trains`: Number of trains to simulate (required)
- `--stations`: Number of stations to include (required)
- `--port`: Starting port number for communication (default: 8080)

Example:
```bash
python simulate.py --trains 2 --stations 2
```

### Training Mode

To train the reinforcement learning model:

```bash
python train.py
```

This will start the Ray RLlib training process using PPO algorithm. The training results and checkpoints will be saved in the `ray_results` directory.

## Analyzing Results

After training or simulation, you can analyze the results using the analysis tools:

```bash
python analysis.py
```

This will generate performance graphs showing:
- Instantaneous rewards
- Cumulative rewards
- Combined reward metrics

The graphs will be saved in the `logs/` directory.

## Project Components

- **Controller**: Manages the train communication and environment state
- **Router**: Handles routing information and update channels
- **Environment**: Represents the railway network and train states
- **RL Environment**: Reinforcement learning interface for training models
- **System**: Coordinates all components and handles system lifecycle

## Troubleshooting

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Ensure Unity is properly installed and the path is correctly set in the `.env` file
3. Verify all dependencies are installed with the correct versions
4. Ensure ports specified are available on your system