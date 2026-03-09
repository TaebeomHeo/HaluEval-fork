import json
import collections
import time
import sys

def stream_analyze(file_path):
    print(f"\n[{time.strftime('%H:%M:%S')}] --- Started Analyzing: {file_path} ---")
    start_time = time.time()
    
    total = 0
    has_error = 0
    correct = 0
    datasets = collections.Counter()
    error_types = collections.Counter()
    tags = ["<entity>", "<relation>", "<contradictory>", "<invented>", "<subjective>", "<unverifiable>"]

    try:
        # We process the list of dicts directly since ijson handles memory iteratively, 
        # but to ensure zero buffering issues, let's load it fully if small enough or use simple iteration
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            for item in data:
                total += 1
                
                # 1. Domain/Dataset
                dataset_name = item.get("dataset", "Unknown")
                datasets[dataset_name] += 1
                
                # 2. Check for Hallucination Tags
                annotated = item.get("annotated", "")
                found_error = False
                for tag in tags:
                    if tag in annotated:
                        error_types[tag.strip("<>")] += 1
                        found_error = True
                
                if found_error:
                    has_error += 1
                else:
                    correct += 1
                    
                # Print progress to console every 5,000 records
                if total % 5000 == 0:
                    elapsed = time.time() - start_time
                    print(f"[{time.strftime('%H:%M:%S')}] Progress: Processed {total} records... ({elapsed:.1f}s elapsed)")
                    sys.stdout.flush()

        # Final Analysis Report
        print(f"\n[{time.strftime('%H:%M:%S')}] --- Analysis Complete for {file_path} ---")
        print(f"Total time taken: {time.time() - start_time:.2f} seconds")
        print(f"Total records processed: {total:,}")
        
        print("\nBreakdown by domain/dataset:")
        for k, v in datasets.most_common():
            print(f"  - {k}: {v:,} ({v/total*100:.1f}%)")
            
        print("\nCorrect vs Hallucinated (Incorrect) Ratio:")
        print(f"  - Clean / Correct (No tags): {correct:,} ({correct/total*100:.1f}%)")
        print(f"  - Hallucinated (Contains tags): {has_error:,} ({has_error/total*100:.1f}%)")
        
        if error_types:
            print("\nHallucination Type Breakdown (Total tag occurrences):")
            for k, v in error_types.most_common():
                print(f"  - {k}: {v:,}")
                
    except Exception as e:
        print(f"\n[ERROR] An error occurred while parsing {file_path}: {e}")

if __name__ == "__main__":
    stream_analyze("ww_custom/fava_data/annotations.json")
    stream_analyze("ww_custom/fava_data/training.json")
