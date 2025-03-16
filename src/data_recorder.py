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
from PyQt5.QtCore import QObject, pyqtSignal

class DataRecorder(QObject):
    # Signals for visualization updates
    traffic_update = pyqtSignal(dict)  # Emits traffic counts by direction
    reward_update = pyqtSignal(int, float)  # Emits (step, reward)
    
    def __init__(self):
        super().__init__()
        self.current_episode = 0
        self.episode_data = []
        self.total_score = 0
        self.achievements = set()
        self.leaderboard_file = "data/leaderboard.csv"
        self.episode_metrics_file = "data/episode_metrics.csv"
        self.light_changes = 0  # Track light changes within episode
        self.simulation = None  # Reference to simulation
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize leaderboard if it doesn't exist
        if not os.path.exists(self.leaderboard_file):
            pd.DataFrame(columns=['date', 'score', 'avg_satisfaction', 'avg_commute']).to_csv(self.leaderboard_file, index=False)
            
        # Initialize episode metrics file if it doesn't exist
        if not os.path.exists(self.episode_metrics_file):
            pd.DataFrame(columns=['episode', 'score', 'avg_satisfaction', 'avg_commute', 'light_changes', 'completion_rate']).to_csv(self.episode_metrics_file, index=False)
    
    def set_simulation(self, simulation):
        """Set the simulation reference"""
        self.simulation = simulation
    
    def record_tick(self, tick, light_state, waiting_count, moving_count, arrived_count, avg_satisfaction):
        """Record data for the current tick"""
        self.episode_data.append({
            'tick': tick,
            'light_state': light_state,
            'waiting_count': waiting_count,
            'moving_count': moving_count,
            'arrived_count': arrived_count,
            'avg_satisfaction': avg_satisfaction,
            'light_changes': self.light_changes  # Add current light changes count
        })
        
        # Get traffic counts from simulation
        if self.simulation:
            traffic_counts = self.simulation.get_traffic_counts()
            # Emit traffic update
            self.traffic_update.emit(traffic_counts)
        
        # Calculate and emit reward
        reward = self.calculate_reward(waiting_count, moving_count, avg_satisfaction)
        self.reward_update.emit(tick, reward)
    
    def calculate_reward(self, waiting_count, moving_count, avg_satisfaction):
        """Calculate reward based on current state"""
        # Reward for vehicles moving (positive)
        moving_reward = moving_count * 0.1
        
        # Penalty for waiting vehicles (negative)
        waiting_penalty = waiting_count * -0.2
        
        # Reward for high satisfaction (positive)
        satisfaction_reward = avg_satisfaction * 0.3
        
        return moving_reward + waiting_penalty + satisfaction_reward
    
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
            
        try:
            df = pd.DataFrame(self.episode_data)
            
            # Create figure with subplots
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
            
            # Plot satisfaction
            ax1.plot(df['tick'], df['avg_satisfaction'], 'b-')
            ax1.set_title('Average Satisfaction Over Time')
            ax1.set_xlabel('Time Steps')
            ax1.set_ylabel('Satisfaction')
            ax1.grid(True)
            
            # Plot traffic flow
            ax2.plot(df['tick'], df['waiting_count'] + df['moving_count'], 'r-')
            ax2.set_title('Total Traffic Flow')
            ax2.set_xlabel('Time Steps')
            ax2.set_ylabel('Vehicles')
            ax2.grid(True)
            
            # Plot light changes
            ax3.plot(df['tick'], df['light_changes'], 'g-')
            ax3.set_title('Light Changes Over Time')
            ax3.set_xlabel('Time Steps')
            ax3.set_ylabel('Number of Changes')
            ax3.grid(True)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save the plot
            plt.savefig('data/learning_curve.png')
            plt.close()
            
        except Exception as e:
            print(f"Error plotting learning curve: {e}")
            import traceback
            traceback.print_exc()
    
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
            import traceback
            traceback.print_exc()

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