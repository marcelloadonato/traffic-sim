"""
Data Recorder for Traffic Simulation

Features:
- Tracks simulation metrics and learning progress
- Records scores and achievements
- Maintains leaderboard of top performances
- Tracks metrics across episodes
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
        self.episode_metrics_file = "data/episode_metrics.csv"
        self.light_changes = 0  # Track light changes within episode
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize leaderboard if it doesn't exist
        if not os.path.exists(self.leaderboard_file):
            pd.DataFrame(columns=['date', 'score', 'avg_satisfaction', 'avg_commute']).to_csv(self.leaderboard_file, index=False)
            
        # Initialize episode metrics file if it doesn't exist
        if not os.path.exists(self.episode_metrics_file):
            pd.DataFrame(columns=['episode', 'score', 'avg_satisfaction', 'avg_commute', 'light_changes', 'completion_rate']).to_csv(self.episode_metrics_file, index=False)
    
    def record_tick(self, tick, light_state, waiting_count, moving_count, arrived_count, avg_satisfaction):
        """Record data for the current tick"""
        try:
            self.episode_data.append({
                'tick': tick,
                'light_state': light_state,
                'waiting_count': waiting_count,
                'moving_count': moving_count,
                'arrived_count': arrived_count,
                'avg_satisfaction': avg_satisfaction,
                'light_changes': self.light_changes  # Add current light changes count
            })
            
            # Update total score based on reward components
            reward = -0.2 * (waiting_count + moving_count) + avg_satisfaction
            self.total_score += reward
        except Exception as e:
            print(f"Error recording tick data: {e}")
    
    def record_light_change(self):
        """Record when a light changes state"""
        self.light_changes += 1
    
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
            completion_rate = max(d['arrived_count'] for d in self.episode_data) / 100  # Assuming max 100 vehicles per episode
        except Exception as e:
            print(f"Error calculating episode statistics: {e}")
            avg_satisfaction = 0
            avg_commute = 0
            completion_rate = 0
        
        # Update leaderboard
        try:
            leaderboard = pd.read_csv(self.leaderboard_file)
            new_entry = pd.DataFrame([{
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'score': self.total_score,
                'avg_satisfaction': avg_satisfaction,
                'avg_commute': avg_commute,
                'light_changes': self.light_changes
            }])
            leaderboard = pd.concat([leaderboard, new_entry], ignore_index=True)
            leaderboard = leaderboard.sort_values('score', ascending=False).head(5)
            leaderboard.to_csv(self.leaderboard_file, index=False)
        except Exception as e:
            print(f"Error updating leaderboard: {e}")
            
        # Update episode metrics
        try:
            episode_metrics = pd.read_csv(self.episode_metrics_file)
            new_episode = pd.DataFrame([{
                'episode': self.current_episode,
                'score': self.total_score,
                'avg_satisfaction': avg_satisfaction,
                'avg_commute': avg_commute,
                'light_changes': self.light_changes,
                'completion_rate': completion_rate
            }])
            episode_metrics = pd.concat([episode_metrics, new_episode], ignore_index=True)
            episode_metrics.to_csv(self.episode_metrics_file, index=False)
        except Exception as e:
            print(f"Error updating episode metrics: {e}")
        
        # Plot learning curves
        try:
            self.plot_learning_curve()
            self.plot_episode_progress()
        except Exception as e:
            print(f"Error plotting learning curves: {e}")
        
        # Reset for next episode
        self.current_episode += 1
        self.episode_data = []
        self.total_score = 0
        self.achievements.clear()
        self.light_changes = 0  # Reset light changes counter
    
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
        plt.plot(df['tick'], df['light_changes'], 'g-')
        plt.title('Light Changes')
        plt.xlabel('Tick')
        plt.ylabel('Number of Changes')
        plt.grid(True)
        plt.savefig('data/light_changes.png')
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
        
        # Third y-axis (far right) for light changes (green)
        ax3 = ax1.twinx()
        # Offset the third axis
        ax3.spines['right'].set_position(('outward', 60))
        ax3.set_ylabel('Light Changes', color='g')
        ln2 = ax3.plot(df['tick'], df['light_changes'], 'g-', label='Light Changes')
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
        
    def plot_episode_progress(self):
        """Plot metrics across episodes to show learning progress"""
        try:
            episode_metrics = pd.read_csv(self.episode_metrics_file)
            if len(episode_metrics) < 2:  # Need at least 2 episodes to plot progress
                return
                
            # Create figure with subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # Plot score progression
            ax1.plot(episode_metrics['episode'], episode_metrics['score'], 'b-')
            ax1.set_title('Episode Score Progression')
            ax1.set_xlabel('Episode')
            ax1.set_ylabel('Score')
            ax1.grid(True)
            
            # Plot satisfaction progression
            ax2.plot(episode_metrics['episode'], episode_metrics['avg_satisfaction'], 'g-')
            ax2.set_title('Average Satisfaction Progression')
            ax2.set_xlabel('Episode')
            ax2.set_ylabel('Satisfaction')
            ax2.grid(True)
            
            # Plot commute time progression
            ax3.plot(episode_metrics['episode'], episode_metrics['avg_commute'], 'r-')
            ax3.set_title('Average Commute Time Progression')
            ax3.set_xlabel('Episode')
            ax3.set_ylabel('Commute Time')
            ax3.grid(True)
            
            # Plot light changes progression
            ax4.plot(episode_metrics['episode'], episode_metrics['light_changes'], 'm-')
            ax4.set_title('Light Changes Progression')
            ax4.set_xlabel('Episode')
            ax4.set_ylabel('Number of Changes')
            ax4.grid(True)
            
            # Add overall title
            plt.suptitle('Learning Progress Across Episodes', fontsize=16)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save the plot
            plt.savefig('data/episode_progress.png')
            plt.close()
            
        except Exception as e:
            print(f"Error plotting episode progress: {e}")

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