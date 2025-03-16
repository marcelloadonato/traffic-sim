import pandas as pd
import matplotlib.pyplot as plt
import os

class DataRecorder:
    def __init__(self):
        self.episode_data = []
        self.current_episode = 1
        self.tick_data = []
        self.episode_summaries = []
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
    def record_tick(self, tick, light_state, waiting_count, moving_count, arrived_count, avg_satisfaction):
        """Record data for a single simulation tick"""
        self.tick_data.append({
            'episode': self.current_episode,
            'tick': tick,
            'light_state': light_state,
            'waiting_vehicles': waiting_count,
            'moving_vehicles': moving_count,
            'arrived_vehicles': arrived_count,
            'avg_satisfaction': avg_satisfaction
        })
        
    def record_vehicle_completion(self, vehicle):
        """Record data when a vehicle completes its journey"""
        self.episode_data.append({
            'episode': self.current_episode,
            'vehicle_id': id(vehicle),
            'vehicle_type': vehicle.vehicle_type,
            'start_position': vehicle.start_position,
            'destination': vehicle.destination,
            'commute_time': vehicle.commute_time,
            'final_satisfaction': vehicle.satisfaction
        })
        
    def end_episode(self, light_change_count):
        """End the current episode and calculate summary statistics"""
        if not self.episode_data:
            return
            
        # Calculate episode summary
        avg_commute = sum(v['commute_time'] for v in self.episode_data) / len(self.episode_data)
        avg_satisfaction = sum(v['final_satisfaction'] for v in self.episode_data) / len(self.episode_data)
        total_vehicles = len(self.episode_data)
        
        # Store summary
        self.episode_summaries.append({
            'episode': self.current_episode,
            'avg_commute_time': avg_commute,
            'avg_satisfaction': avg_satisfaction,
            'total_vehicles': total_vehicles,
            'light_changes': light_change_count,
            'reward': -0.1 * avg_commute + avg_satisfaction  # Example reward function
        })
        
        # Save data to files
        self.save_data()
        
        # Prepare for next episode
        self.current_episode += 1
        self.episode_data = []
        self.tick_data = []
        
    def save_data(self):
        """Save collected data to CSV files"""
        # Save episode data
        if self.episode_data:
            pd.DataFrame(self.episode_data).to_csv(f'data/episode_{self.current_episode}_vehicles.csv', index=False)
        
        # Save tick data
        if self.tick_data:
            pd.DataFrame(self.tick_data).to_csv(f'data/episode_{self.current_episode}_ticks.csv', index=False)
        
        # Save episode summaries
        if self.episode_summaries:
            pd.DataFrame(self.episode_summaries).to_csv('data/episode_summaries.csv', index=False)
            
    def plot_learning_curve(self):
        """Generate separate plots and a combined plot with triple y-axes for all metrics"""
        if not self.episode_summaries:
            return
            
        df = pd.DataFrame(self.episode_summaries)
        
        # Individual plots
        plt.figure(figsize=(10, 6))
        plt.plot(df['episode'], df['reward'], 'b-')
        plt.title('Reward per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.grid(True)
        plt.savefig('data/reward_curve.png')
        plt.close()
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['episode'], df['avg_commute_time'], 'r-')
        plt.title('Average Commute Time per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Ticks')
        plt.grid(True)
        plt.savefig('data/commute_time_curve.png')
        plt.close()
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['episode'], df['avg_satisfaction'], 'g-')
        plt.title('Average Satisfaction per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Satisfaction (0-10)')
        plt.grid(True)
        plt.savefig('data/satisfaction_curve.png')
        plt.close()
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['episode'], df['light_changes'], 'm-')
        plt.title('Number of Light Changes per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Light Changes')
        plt.grid(True)
        plt.savefig('data/light_changes_curve.png')
        plt.close()
        
        # Combined plot with quadruple y-axes
        fig, ax1 = plt.subplots(figsize=(12, 8))
        
        # Primary y-axis (left) for reward (blue)
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Reward', color='b')
        ax1.plot(df['episode'], df['reward'], 'b-', label='Reward')
        ax1.tick_params(axis='y', labelcolor='b')
        
        # Secondary y-axis (right) for commute time (red)
        ax2 = ax1.twinx()
        ax2.set_ylabel('Commute Time', color='r')
        ln1 = ax2.plot(df['episode'], df['avg_commute_time'], 'r-', label='Avg Commute Time')
        ax2.tick_params(axis='y', labelcolor='r')
        
        # Third y-axis (far right) for satisfaction (green)
        ax3 = ax1.twinx()
        # Offset the third axis
        ax3.spines['right'].set_position(('outward', 60))
        ax3.set_ylabel('Satisfaction (0-10)', color='g')
        ln2 = ax3.plot(df['episode'], df['avg_satisfaction'], 'g-', label='Avg Satisfaction')
        ax3.tick_params(axis='y', labelcolor='g')
        
        # Fourth y-axis (far right) for light changes (magenta)
        ax4 = ax1.twinx()
        # Offset the fourth axis
        ax4.spines['right'].set_position(('outward', 120))
        ax4.set_ylabel('Light Changes', color='m')
        ln3 = ax4.plot(df['episode'], df['light_changes'], 'm-', label='Light Changes')
        ax4.tick_params(axis='y', labelcolor='m')
        
        # Set satisfaction y-axis limits to 0-10
        ax3.set_ylim(0, 10)
        
        # Add title and grid
        plt.title('Combined Metrics per Episode')
        ax1.grid(True)
        
        # Combine legends from all axes
        lns = [ax1.get_lines()[0]] + ln1 + ln2 + ln3
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc='upper right')
        
        # Adjust layout to prevent label overlap
        plt.tight_layout()
        
        plt.savefig('data/combined_curves.png')
        plt.close() 