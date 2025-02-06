import argparse
import numpy as np

def main():
    parser = argparse.ArgumentParser(description='TGV Results Comparator')
    parser.add_argument('--current', required=True, help='Current results file')
    parser.add_argument('--reference', required=True, help='Reference results file')
    parser.add_argument('--tolerance', type=float, default=1e-4, 
                        help='Relative tolerance for comparison')
    args = parser.parse_args()

    # Load data with proper parsing
    current = np.genfromtxt(args.current, delimiter=',', skip_header=1)
    reference = np.genfromtxt(args.reference, delimiter=',', skip_header=1)
    
    if current.shape != reference.shape:
        print(f"ERROR: Shape mismatch {current.shape} vs {reference.shape}")
        exit(1)

    max_diff = 0.0
    for i in range(current.shape[0]):
        for j in range(current.shape[1]):
            denom = abs(reference[i, j]) + args.tolerance  # Avoid division by zero
            rel_diff = abs(current[i, j] - reference[i, j]) / denom
            
            if rel_diff > args.tolerance:
                print(f"Mismatch at ({i},{j}): {rel_diff:.2e} > {args.tolerance:.0e}")
                exit(1)
                
            max_diff = max(max_diff, rel_diff)
    
    print(f"All results match within tolerance {args.tolerance:.0e}")
    print(f"Maximum relative difference: {max_diff:.2e}")
    print(f"Compared {current.shape[0]} timesteps successfully")

if __name__ == "__main__":
    main()
