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
        
    def end_episode(self):
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
        """Generate separate plots for reward, commute time, and satisfaction"""
        if not self.episode_summaries:
            return
            
        df = pd.DataFrame(self.episode_summaries)
        
        # Plot 1: Reward per episode
        plt.figure(figsize=(10, 6))
        plt.plot(df['episode'], df['reward'], 'b-')
        plt.title('Reward per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.grid(True)
        plt.savefig('data/reward_curve.png')
        plt.close()
        
        # Plot 2: Average commute time
        plt.figure(figsize=(10, 6))
        plt.plot(df['episode'], df['avg_commute_time'], 'r-')
        plt.title('Average Commute Time per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Ticks')
        plt.grid(True)
        plt.savefig('data/commute_time_curve.png')
        plt.close()
        
        # Plot 3: Average satisfaction
        plt.figure(figsize=(10, 6))
        plt.plot(df['episode'], df['avg_satisfaction'], 'g-')
        plt.title('Average Satisfaction per Episode')
        plt.xlabel('Episode')
        plt.ylabel('Satisfaction (0-10)')
        plt.grid(True)
        plt.savefig('data/satisfaction_curve.png')
        plt.close() 