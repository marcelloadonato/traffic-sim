"""
Data Recorder for Traffic Simulation

Features:
- Tracks simulation metrics and learning progress
- Records scores and achievements
- Maintains leaderboard of top performances
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

class DataRecorder:
    def __init__(self):
        self.current_episode = 0
        self.episode_data = []
        self.total_score = 0
        self.achievements = set()
        self.leaderboard_file = "data/leaderboard.csv"
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize leaderboard if it doesn't exist
        if not os.path.exists(self.leaderboard_file):
            pd.DataFrame(columns=['date', 'score', 'avg_satisfaction', 'avg_commute']).to_csv(self.leaderboard_file, index=False)
    
    def record_tick(self, tick, light_state, waiting_count, moving_count, arrived_count, avg_satisfaction):
        """Record data for the current tick"""
        try:
            self.episode_data.append({
                'tick': tick,
                'light_state': light_state,
                'waiting_count': waiting_count,
                'moving_count': moving_count,
                'arrived_count': arrived_count,
                'avg_satisfaction': avg_satisfaction
            })
            
            # Update total score based on reward components
            reward = -0.2 * (waiting_count + moving_count) + avg_satisfaction
            self.total_score += reward
        except Exception as e:
            print(f"Error recording tick data: {e}")
    
    def record_vehicle_completion(self, vehicle):
        """Record data when a vehicle completes its journey"""
        # Check for "All Clear!" achievement
        if vehicle.state == "arrived" and not self.active_vehicles:
            self.achievements.add("All Clear!")
    
    def end_episode(self, light_change_count=None):
        """End the current episode and save data"""
        # Handle empty episode data
        if not self.episode_data:
            print("Warning: No episode data recorded")
            return
            
        # Calculate episode statistics
        try:
            avg_satisfaction = sum(d['avg_satisfaction'] for d in self.episode_data) / len(self.episode_data)
            avg_commute = sum(d['waiting_count'] + d['moving_count'] for d in self.episode_data) / len(self.episode_data)
        except Exception as e:
            print(f"Error calculating episode statistics: {e}")
            avg_satisfaction = 0
            avg_commute = 0
        
        # Update leaderboard
        try:
            leaderboard = pd.read_csv(self.leaderboard_file)
            new_entry = pd.DataFrame([{
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'score': self.total_score,
                'avg_satisfaction': avg_satisfaction,
                'avg_commute': avg_commute,
                'light_changes': light_change_count if light_change_count is not None else 0
            }])
            leaderboard = pd.concat([leaderboard, new_entry], ignore_index=True)
            leaderboard = leaderboard.sort_values('score', ascending=False).head(5)
            leaderboard.to_csv(self.leaderboard_file, index=False)
        except Exception as e:
            print(f"Error updating leaderboard: {e}")
        
        # Plot learning curve
        try:
            self.plot_learning_curve()
        except Exception as e:
            print(f"Error plotting learning curve: {e}")
        
        # Reset for next episode
        self.current_episode += 1
        self.episode_data = []
        self.total_score = 0
        self.achievements.clear()
    
    def plot_learning_curve(self):
        """Plot learning curve from recorded data"""
        if not self.episode_data:
            return
        
        plt.figure(figsize=(10, 6))
        plt.plot([d['tick'] for d in self.episode_data], 
                [d['avg_satisfaction'] for d in self.episode_data])
        plt.title('Learning Curve')
        plt.xlabel('Tick')
        plt.ylabel('Average Satisfaction')
        plt.savefig('data/learning_curve.png')
        plt.close()

    def save_data(self):
        """Save collected data to CSV files"""
        # Save episode data
        if self.episode_data:
            pd.DataFrame(self.episode_data).to_csv(f'data/episode_{self.current_episode}_vehicles.csv', index=False)
        
        # Save tick data
        if self.episode_data:
            pd.DataFrame(self.episode_data).to_csv(f'data/episode_{self.current_episode}_ticks.csv', index=False)
        
        # Save episode summaries
        if self.episode_data:
            pd.DataFrame(self.episode_data).to_csv('data/episode_summaries.csv', index=False)
            
    def plot_learning_curve(self):
        """Generate separate plots and a combined plot with triple y-axes for all metrics"""
        if not self.episode_data:
            return
            
        df = pd.DataFrame(self.episode_data)
        
        # Individual plots
        plt.figure(figsize=(10, 6))
        plt.plot(df['tick'], df['avg_satisfaction'], 'b-')
        plt.title('Learning Curve')
        plt.xlabel('Tick')
        plt.ylabel('Average Satisfaction')
        plt.grid(True)
        plt.savefig('data/learning_curve.png')
        plt.close()
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['tick'], df['waiting_count'] + df['moving_count'], 'r-')
        plt.title('Traffic Flow')
        plt.xlabel('Tick')
        plt.ylabel('Vehicles')
        plt.grid(True)
        plt.savefig('data/traffic_flow.png')
        plt.close()
        
        plt.figure(figsize=(10, 6))
        plt.plot(df['tick'], df['light_state'], 'g-')
        plt.title('Light State')
        plt.xlabel('Tick')
        plt.ylabel('Light')
        plt.grid(True)
        plt.savefig('data/light_state.png')
        plt.close()
        
        # Combined plot with quadruple y-axes
        fig, ax1 = plt.subplots(figsize=(12, 8))
        
        # Primary y-axis (left) for satisfaction (blue)
        ax1.set_xlabel('Tick')
        ax1.set_ylabel('Satisfaction', color='b')
        ax1.plot(df['tick'], df['avg_satisfaction'], 'b-', label='Satisfaction')
        ax1.tick_params(axis='y', labelcolor='b')
        
        # Secondary y-axis (right) for traffic flow (red)
        ax2 = ax1.twinx()
        ax2.set_ylabel('Traffic Flow', color='r')
        ln1 = ax2.plot(df['tick'], df['waiting_count'] + df['moving_count'], 'r-', label='Traffic Flow')
        ax2.tick_params(axis='y', labelcolor='r')
        
        # Third y-axis (far right) for light state (green)
        ax3 = ax1.twinx()
        # Offset the third axis
        ax3.spines['right'].set_position(('outward', 60))
        ax3.set_ylabel('Light State', color='g')
        ln2 = ax3.plot(df['tick'], df['light_state'], 'g-', label='Light State')
        ax3.tick_params(axis='y', labelcolor='g')
        
        # Add title and grid
        plt.title('Traffic Simulation Metrics')
        ax1.grid(True)
        
        # Combine legends from all axes
        lns = [ax1.get_lines()[0]] + ln1 + ln2
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc='upper right')
        
        # Adjust layout to prevent label overlap
        plt.tight_layout()
        
        plt.savefig('data/combined_metrics.png')
        plt.close() 