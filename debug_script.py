import sys
import traceback
sys.path.insert(0, '.')
try:
    from src.main import main
    main()
except Exception as e:
    with open('error_log.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    print("Error occurred. Check error_log.txt")
    input("Press Enter to exit...")