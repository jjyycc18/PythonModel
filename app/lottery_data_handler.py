"""
Lottery Data Handler Module

This module provides functionality to load, parse, and validate lottery data from CSV files.
It handles the core data operations for the lottery analyzer application.
"""

import csv
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LotteryDraw:
    """Represents a single lottery draw with validation."""
    count: int
    numbers: List[int]
    bonus: Optional[int] = None
    
    def __post_init__(self):
        """Validate lottery draw data after initialization."""
        if not isinstance(self.count, int) or self.count < 1:
            raise ValueError(f"Invalid count: {self.count}. Must be a positive integer.")
        
        if not isinstance(self.numbers, list) or len(self.numbers) != 6:
            raise ValueError(f"Invalid numbers: {self.numbers}. Must be a list of 6 integers.")
        
        for num in self.numbers:
            if not isinstance(num, int) or not (1 <= num <= 45):
                raise ValueError(f"Invalid lottery number: {num}. Must be between 1 and 45.")
        
        if len(set(self.numbers)) != len(self.numbers):
            raise ValueError(f"Duplicate numbers found: {self.numbers}. All numbers must be unique.")
        
        if self.bonus is not None:
            if not isinstance(self.bonus, int) or not (1 <= self.bonus <= 45):
                raise ValueError(f"Invalid bonus number: {self.bonus}. Must be between 1 and 45.")
            if self.bonus in self.numbers:
                raise ValueError(f"Bonus number {self.bonus} cannot be in main numbers: {self.numbers}")


class LotteryDataHandler:
    """Handles loading, parsing, and validation of lottery data from CSV files."""
    
    def __init__(self):
        """Initialize the lottery data handler."""
        self._data: List[LotteryDraw] = []
        self._loaded_file: Optional[str] = None
    
    def load_data(self, filename: str) -> List[LotteryDraw]:
        """
        Load and parse lottery data from a CSV file.
        
        Args:
            filename: Path to the CSV file containing lottery data
            
        Returns:
            List of LotteryDraw objects
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            ValueError: If the CSV data is invalid or malformed
            IOError: If there's an error reading the file
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"CSV file not found: {filename}")
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                # Validate CSV headers
                expected_headers = {'count', 'aa', 'bb', 'cc', 'dd', 'ee', 'ff'}
                if not expected_headers.issubset(set(csv_reader.fieldnames or [])):
                    raise ValueError(f"Invalid CSV headers. Expected: {expected_headers}, "
                                   f"Found: {csv_reader.fieldnames}")
                
                data = []
                for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
                    try:
                        draw = self._parse_csv_row(row)
                        data.append(draw)
                    except ValueError as e:
                        raise ValueError(f"Error in row {row_num}: {e}")
                
                if not data:
                    raise ValueError("No valid data found in CSV file")
                
                self._data = data
                self._loaded_file = filename
                return data
                
        except IOError as e:
            raise IOError(f"Error reading file {filename}: {e}")
    
    def _parse_csv_row(self, row: Dict[str, str]) -> LotteryDraw:
        """
        Parse a single CSV row into a LotteryDraw object.
        
        Args:
            row: Dictionary representing a CSV row
            
        Returns:
            LotteryDraw object
            
        Raises:
            ValueError: If the row data is invalid
        """
        try:
            count = int(row['count'])
            numbers = [
                int(row['aa']),
                int(row['bb']),
                int(row['cc']),
                int(row['dd']),
                int(row['ee']),
                int(row['ff'])
            ]
            
            # Handle bonus number if present (sum column might be bonus)
            bonus = None
            if 'sum' in row and row['sum'].strip():
                try:
                    bonus = int(row['sum'])
                    # Only treat as bonus if it's a valid lottery number
                    if not (1 <= bonus <= 45):
                        bonus = None
                except ValueError:
                    bonus = None
            
            return LotteryDraw(count=count, numbers=numbers, bonus=bonus)
            
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid row data: {row}. Error: {e}")
    
    def get_historical_range(self, start_count: int, end_count: int) -> List[LotteryDraw]:
        """
        Get lottery draws within a specific count range.
        
        Args:
            start_count: Starting count number (inclusive)
            end_count: Ending count number (inclusive)
            
        Returns:
            List of LotteryDraw objects within the specified range
            
        Raises:
            ValueError: If range parameters are invalid
            RuntimeError: If no data has been loaded
        """
        if not self._data:
            raise RuntimeError("No data loaded. Call load_data() first.")
        
        if start_count > end_count:
            raise ValueError(f"Invalid range: start_count ({start_count}) > end_count ({end_count})")
        
        if start_count < 1:
            raise ValueError(f"Invalid start_count: {start_count}. Must be positive.")
        
        filtered_data = [
            draw for draw in self._data 
            if start_count <= draw.count <= end_count
        ]
        
        # Sort by count in ascending order
        filtered_data.sort(key=lambda x: x.count)
        
        return filtered_data
    
    def validate_data_integrity(self) -> Tuple[bool, List[str]]:
        """
        Validate the integrity of loaded data.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if not self._data:
            return False, ["No data loaded"]
        
        errors = []
        counts = [draw.count for draw in self._data]
        
        # Check for duplicate counts
        if len(counts) != len(set(counts)):
            duplicates = [count for count in set(counts) if counts.count(count) > 1]
            errors.append(f"Duplicate draw counts found: {duplicates}")
        
        # Check for missing counts in expected range
        if counts:
            min_count, max_count = min(counts), max(counts)
            expected_counts = set(range(min_count, max_count + 1))
            actual_counts = set(counts)
            missing = expected_counts - actual_counts
            if missing:
                errors.append(f"Missing draw counts: {sorted(missing)}")
        
        return len(errors) == 0, errors
    
    def get_data_summary(self) -> Dict[str, any]:
        """
        Get a summary of the loaded data.
        
        Returns:
            Dictionary containing data summary information
        """
        if not self._data:
            return {"loaded": False, "count": 0}
        
        counts = [draw.count for draw in self._data]
        all_numbers = []
        for draw in self._data:
            all_numbers.extend(draw.numbers)
        
        return {
            "loaded": True,
            "file": self._loaded_file,
            "total_draws": len(self._data),
            "count_range": (min(counts), max(counts)) if counts else None,
            "total_numbers": len(all_numbers),
            "unique_numbers": len(set(all_numbers)),
            "number_range": (min(all_numbers), max(all_numbers)) if all_numbers else None
        }
