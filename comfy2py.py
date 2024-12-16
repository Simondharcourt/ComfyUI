import os
import json
import argparse
import execution
from urllib import request
import random

# This is the default path to save your workflows from ComfyUI
# Workflow should be savec in their API format


DEFAULT_WORKFLOW_PATH = "/Users/simondharcourt/Downloads"

class Workflow:
    """
    A class to handle ComfyUI workflow files.
    This class provides functionality to load, modify and execute ComfyUI workflows.
    It can update prompts, steps, seeds and other workflow parameters.
    """

    def __init__(self, workflow_name):
        """
        Initialize a Workflow object.
        Args:
            workflow_name (str): Name of the workflow JSON file
        Raises:
            ValueError: If the workflow is not valid
        """
        self.workflow_name = workflow_name
        self.workflow_data = self.load_workflow()
        if not self.is_valid():
            raise ValueError(f"Workflow {self.workflow_name} is not valid")
        
    def is_valid(self):
        """
        Check if the workflow is valid.
        Returns:
            bool: True if workflow is valid, False otherwise
        """
        valid = execution.validate_prompt(self.workflow_data)
        return valid

    def load_workflow(self):
        """
        Load workflow data from JSON file.
        Returns:
            dict: Workflow data as dictionary            
        Raises:
            FileNotFoundError: If workflow file is not found
        """
        if not self.workflow_name.endswith('.json'):
            self.workflow_name += '.json'
        workflow_path = os.path.join(DEFAULT_WORKFLOW_PATH, self.workflow_name)
        if not os.path.exists(workflow_path):
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
        with open(workflow_path, 'r') as f:
            return json.load(f)

    def get_prompt_node_id(self, tone: str) -> str:
        """
        Get the node ID for a prompt of specified tone.
        Args:
            tone (str): Either 'positive' or 'negative'
        Returns:
            str: Node ID if found, None otherwise
        Raises:
            ValueError: If tone is not 'positive' or 'negative'
        """
        if tone not in ['positive', 'negative']:
            raise ValueError("tone should be 'positive' or 'negative'.")
        for node in self.workflow_data:
            if tone in self.workflow_data[node]['inputs']:
                node_id = self.workflow_data[node]['inputs'][tone][0]
                return node_id
        return None

    def update_positive_prompt(self, prompt): 
        """
        Update the positive prompt text in the workflow.
        Args:
            prompt (str): New positive prompt text
        """
        positive_node_id = self.get_prompt_node_id('positive')
        if positive_node_id is not None:
            self.workflow_data[positive_node_id]['inputs']['text'] = prompt
        else:
            print("No positive node found")

    def update_negative_prompt(self, prompt):
        """
        Update the negative prompt text in the workflow.
        Args:
            prompt (str): New negative prompt text
        """
        negative_node_id = self.get_prompt_node_id('negative')
        if negative_node_id is not None:
            self.workflow_data[negative_node_id]['inputs']['text'] = prompt
        else:
            print("No negative node found")
        
    def show_prompts(self):
        """Display both positive and negative prompts from the workflow."""
        positive_node_id = self.get_prompt_node_id('positive')
        negative_node_id = self.get_prompt_node_id('negative')
        if positive_node_id is not None:
            print(f"Positive prompt: {self.workflow_data[positive_node_id]['inputs']['text']}")
        if negative_node_id is not None:
            print(f"Negative prompt: {self.workflow_data[negative_node_id]['inputs']['text']}")
            
    def get_node_id(self, node_type: str) -> str:
        """
        Get node ID for a specific node type.

        Args:
            node_type (str): Type of node to find
        Returns:
            str: Node ID
        Raises:
            ValueError: If no node of specified type is found
        """
        for node in self.workflow_data:
            if node_type in self.workflow_data[node]['inputs']:
                node_id = self.workflow_data[node]['inputs'][node_type][0]
                return node_id
        raise ValueError("No node found")
            
    def print_model(self):
        """Display the model checkpoint name used in the workflow."""
        model_node_id = self.get_node_id('model')
        if model_node_id is not None:
            print(f"Model: {self.workflow_data[model_node_id]['inputs']['ckpt_name']}")

    def queue_prompt(self, server_adress):
        """
        Queue the workflow for execution on ComfyUI server.
        Args:
            server_adress (str): Address of ComfyUI server
        """
        prompt = {"prompt": self.workflow_data}
        data = json.dumps(prompt).encode('utf-8')
        req =  request.Request(f"http://{server_adress}/prompt", data=data)
        # print(json.loads(request.urlopen(req).read()))

    def describe(self):
        """Print the complete workflow data structure."""
        import pprint
        pprint.pprint(self.workflow_data)

    def update_steps(self, steps: int = None):
        """
        Update the number of sampling steps in the workflow.
        Args:
            steps (int): New number of steps
        """
        for node in self.workflow_data:
            if "steps" in self.workflow_data[node]['inputs']:
                self.workflow_data[node]['inputs']['steps'] = steps
                

    def update_seed(self, seed: int) -> str:
        """
        Update the random seed in the workflow.
        Args:
            seed (int): New seed value (-1 for random)
        """
        for node in self.workflow_data:
            if "seed" in self.workflow_data[node]['inputs']:
                if seed == -1:
                    self.workflow_data[node]['inputs']['seed'] = random.randint(0, 1000000)
                else:
                    self.workflow_data[node]['inputs']['seed'] = seed

    def save_workflow(self, workflow_name: str = None):
        """
        Save the workflow to a JSON file.
        Args:
            workflow_name (str, optional): Name for the saved workflow file
        """
        if workflow_name is None:
            workflow_name = self.workflow_name
        if not workflow_name.endswith('.json'):
            workflow_name += '.json'
        with open(os.path.join(DEFAULT_WORKFLOW_PATH, workflow_name), 'w') as f:
            json.dump(self.workflow_data, f)

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Execute ComfyUI workflows from command line')
    parser.add_argument('--workflow', type=str, required=True, help='Name of the workflow JSON file')
    parser.add_argument('--prompt', type=str, help='Override positive prompt text')
    parser.add_argument('--neg-prompt', type=str, help='Override negative prompt text')
    parser.add_argument('--steps', type=int, help='Override number of sampling steps')
    parser.add_argument('--seed', type=int, help='Override seed (-1 for random)')
    parser.add_argument('--port', type=int, default=8188, help='ComfyUI server port')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='ComfyUI server host')
    parser.add_argument('--save', type=str, help='Save the workflow to a file')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    server_address = f"{args.host}:{args.port}"
    workflow = Workflow(args.workflow)    
    if args.prompt:
        workflow.update_positive_prompt(args.prompt)
    if args.neg_prompt:
        workflow.update_negative_prompt(args.neg_prompt)
    if args.steps:
        workflow.update_steps(args.steps)
    if args.seed:
        workflow.update_seed(args.seed)
    if args.save:
        workflow.save_workflow(args.save)
    workflow.queue_prompt(server_address)
