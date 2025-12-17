#!/usr/bin/env python
"""
GameTime Command Line Interface

This module provides a command-line interface for running GameTime analysis
on C programs to determine worst-case execution time (WCET).
"""

import argparse
import os
import sys
import shutil
from typing import Optional

# Add the src directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project_configuration import ProjectConfiguration
from project_configuration_parser import YAMLConfigurationParser
from analyzer import Analyzer
from defaults import logger
from gametime_error import GameTimeError
from nx_helper import write_dag_to_dot_file


def find_config_file(path: str) -> Optional[str]:
    """
    Find the config.yaml file in the given path.
    
    Parameters:
        path: str
            Path to search for config file (can be a directory or a file)
    
    Returns:
        Optional[str]: Path to config.yaml if found, None otherwise
    """
    # If path is a file and it's a yaml file, return it
    if os.path.isfile(path) and path.endswith(('.yaml', '.yml')):
        return path
    
    # If path is a directory, look for config.yaml
    if os.path.isdir(path):
        config_path = os.path.join(path, 'config.yaml')
        if os.path.exists(config_path):
            return config_path
        
        # Also try config.yml
        config_path = os.path.join(path, 'config.yml')
        if os.path.exists(config_path):
            return config_path
    
    return None


def run_gametime(config_path: str, clean_temp: bool = True, backend: str = None, visualize_weights: bool = False) -> int:
    """
    Run GameTime analysis on the specified configuration.
    
    Parameters:
        config_path: str
            Path to the configuration file
        clean_temp: bool
            Whether to clean temporary files before running (default: True)
        backend: str
            Override backend from config (default: None, use config value)
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse the configuration file
        logger.info(f"Loading configuration from: {config_path}")
        project_config: ProjectConfiguration = YAMLConfigurationParser.parse(config_path)
        
        # Override backend if specified
        if backend:
            logger.info(f"Overriding backend with: {backend}")
            project_config.backend = backend
        
        # Check if backend is specified
        if not project_config.backend:
            # FIXME: Why does logger.error produce duplicate messages.
            logger.error("Error: No backend specified!")
            logger.error("Please specify a backend in the config file or use --backend option")
            logger.error("Available backends: flexpret, x86, arm")
            return 1
        
        # Clean temporary directory if requested
        if clean_temp and os.path.exists(project_config.location_temp_dir):
            logger.info(f"Cleaning temporary directory: {project_config.location_temp_dir}")
            shutil.rmtree(project_config.location_temp_dir)
        
        # Create the analyzer
        logger.info("Creating analyzer...")
        analyzer: Analyzer = Analyzer(project_config)
        
        # Create the DAG
        logger.info("Creating control flow graph (DAG)...")
        analyzer.create_dag()
        
        # Generate basis paths
        logger.info("Generating basis paths...")
        basis_paths = analyzer.generate_basis_paths()
        
        if not basis_paths or len(basis_paths) == 0:
            logger.error("No basis paths were found!")
            return 1
        
        logger.info(f"Found {len(basis_paths)} basis path(s)")
        
        # Measure basis paths
        logger.info("Measuring basis paths...")
        for i, path in enumerate(basis_paths):
            value = path.get_measured_value()
            logger.info(f"  Basis path {i}: {path.name} = {value}")
        
        # Generate additional paths for analysis
        logger.info("Generating additional paths for analysis...")
        generated_paths = analyzer.generate_paths()
        logger.info(f"Generated {len(generated_paths)} path(s) for measurement")
        
        # Measure generated paths
        logger.info("Measuring generated paths...")
        results = []
        for i, path in enumerate(generated_paths):
            output_name: str = f'path{i}'
            value = analyzer.measure_path(path, output_name)
            results.append((path.name, value))
        
        # Display results
        logger.info("\n" + "="*60)
        logger.info("GAMETIME ANALYSIS RESULTS")
        logger.info("="*60)
        logger.info(f"Function analyzed: {project_config.func}")
        logger.info(f"Backend: {project_config.backend if project_config.backend else 'default'}")
        logger.info(f"Number of basis paths: {len(basis_paths)}")
        logger.info(f"Number of generated paths: {len(generated_paths)}")
        
        logger.info("\nBasis Paths:")
        for i, path in enumerate(basis_paths):
            logger.info(f"  {i}: {path.name} = {path.get_measured_value()}")
        
        if results:
            logger.info("\nGenerated Paths:")
            max_value = max(value for _, value in results)
            max_path = [name for name, value in results if value == max_value][0]
            
            for i, (name, value) in enumerate(results):
                marker = " *WCET*" if value == max_value else ""
                logger.info(f"  {i}: {name} = {value}{marker}")
            
            logger.info(f"\nWorst-Case Execution Time (WCET): {max_value}")
            logger.info(f"WCET Path: {max_path}")
        
        logger.info("="*60)
        
        # Visualize weighted graph if requested
        if visualize_weights:
            logger.info("\n" + "="*60)
            logger.info("GENERATING WEIGHTED GRAPH DOT FILE")
            logger.info("="*60)
            
            # Estimate edge weights
            logger.info("Estimating edge weights...")
            analyzer.estimate_edge_weights()
            
            # Create output directory for visualizations
            # Use the project root's visualizations directory (similar to test file)
            config_dir = os.path.dirname(os.path.abspath(config_path))
            # Go up to project root and use visualizations directory there
            # This matches the test file's approach: ../../visualizations from test location
            output_dir = os.path.join(config_dir, '..', '..', 'visualizations')
            output_dir = os.path.abspath(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename based on function name and backend
            func_name = project_config.func.replace(' ', '_').lower()
            backend_name = project_config.backend if project_config.backend else 'default'
            dot_filename = f'{func_name}_{backend_name}_weighted_graph.dot'
            dot_path = os.path.join(output_dir, dot_filename)
            
            # Create edge labels with weights
            edge_labels = {}
            edge_list = list(analyzer.dag.all_edges)
            for i in range(len(analyzer.dag.edge_weights)):
                if i < len(edge_list):
                    edge = edge_list[i]
                    weight = analyzer.dag.edge_weights[i]
                    if abs(weight) > 0.01:  # Only label non-zero weights
                        edge_labels[edge] = f'{weight:.2f}'
                    else:  # Add zero weights too to avoid KeyError
                        edge_labels[edge] = '0.00'
            
            logger.info(f"Creating weighted graph DOT file...")
            write_dag_to_dot_file(analyzer.dag, dot_path, edges_to_labels=edge_labels)
            logger.info(f"DOT file saved to: {dot_path}")
            logger.info("="*60)
        
        logger.info("\nAnalysis completed successfully!")
        
        return 0
        
    except GameTimeError as e:
        logger.error(f"GameTime Error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point for the GameTime CLI."""
    parser = argparse.ArgumentParser(
        description='GameTime - Worst-Case Execution Time (WCET) Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run analysis on a folder containing config.yaml
  gametime /path/to/test/folder

  # Run analysis with a specific config file
  gametime /path/to/config.yaml

  # Run analysis with a specific backend
  gametime /path/to/test/folder --backend x86

  # Run analysis without cleaning temporary files
  gametime /path/to/test/folder --no-clean

  # Run analysis and generate weighted graph visualization
  gametime /path/to/test/folder --visualize-weights
        """
    )
    
    parser.add_argument(
        'path',
        help='Path to test folder (containing config.yaml) or path to config file'
    )
    
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Do not clean temporary files before running'
    )
    
    parser.add_argument(
        '-b', '--backend',
        choices=['flexpret', 'x86', 'arm'],
        help='Backend to use for execution (overrides config file)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='GameTime 0.1.0'
    )
    
    parser.add_argument(
        '--visualize-weights',
        action='store_true',
        help='Generate a DOT file visualizing the weighted graph with estimated edge weights'
    )
    
    args = parser.parse_args()
    
    # Validate the path
    if not os.path.exists(args.path):
        logger.error(f"Error: Path does not exist: {args.path}")
        return 1
    
    # Find the config file
    config_path = find_config_file(args.path)
    if not config_path:
        logger.error(f"Error: Could not find config.yaml in: {args.path}")
        logger.error("Please ensure the directory contains a config.yaml or config.yml file")
        return 1
    
    # Run GameTime analysis
    exit_code = run_gametime(
        config_path,
        clean_temp=not args.no_clean,
        backend=args.backend,
        visualize_weights=args.visualize_weights
    )
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())

