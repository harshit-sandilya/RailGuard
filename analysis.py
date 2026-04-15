import matplotlib.pyplot as plt
import numpy as np


def read_rewards():
    """Read the rewards data from the numpy file."""
    try:
        rewards = np.load("logs/rewards.npy")
        print(f"Loaded rewards with shape: {rewards.shape}")
        return rewards
    except FileNotFoundError:
        print("Error: logs/rewards.npy file not found.")
        return None
    except Exception as e:
        print(f"Error loading rewards file: {e}")
        return None


if __name__ == "__main__":
    rewards_data = read_rewards()
    if rewards_data is not None:
        print(f"Mean reward: {np.mean(rewards_data)}")
        print(f"Max reward: {np.max(rewards_data)}")
        print(f"Min reward: {np.min(rewards_data)}")
        plt.figure(figsize=(10, 6))
        plt.scatter(range(len(rewards_data)), rewards_data, s=0.1, alpha=0.5)
        plt.title("Instantaneous Rewards over time")
        plt.xlabel("Episode")
        plt.ylabel("Reward")
        plt.grid(True, alpha=0.3)
        plt.savefig("logs/inst_rewards.png")
        plt.close()

        # Calculate cumulative rewards with discount factor 0.99
        cumulative_rewards = np.zeros_like(rewards_data)
        cumulative_rewards[0] = rewards_data[0]
        for i in range(1, len(rewards_data)):
            cumulative_rewards[i] = rewards_data[i] + 0.99 * cumulative_rewards[i - 1]

        # Plot cumulative rewards
        plt.figure(figsize=(10, 6))
        plt.scatter(
            range(len(cumulative_rewards)),
            cumulative_rewards,
            s=0.1,
            alpha=0.5,
            color="red",
        )
        plt.title("Cumulative Rewards over time")
        plt.xlabel("Episode")
        plt.ylabel("Cumulative Reward")
        plt.grid(True, alpha=0.3)
        plt.savefig("logs/cumulative_rewards.png")
        plt.close()

        # Plot both rewards on the same figure
        plt.figure(figsize=(10, 6))
        plt.scatter(
            range(len(rewards_data)),
            rewards_data,
            s=0.1,
            alpha=0.5,
            label="Instantaneous Rewards",
        )
        plt.scatter(
            range(len(cumulative_rewards)),
            cumulative_rewards,
            s=0.1,
            alpha=0.5,
            color="red",
            label="Cumulative Rewards",
        )
        plt.title("Instantaneous vs Cumulative Rewards")
        plt.xlabel("Episode")
        plt.ylabel("Reward")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("logs/combined_rewards.png")
        plt.close("all")
