# Model Architecture Sweeping

In ModelBuilding.ipynb, as you can see I have 4 configurations (A, B, C, D) to test for my model CNN. However, I also have to test a variety of CNN architectures in themselves. Currently I only have BirdCNN as you can see in models.py, but I want to test more architectures and variety in them to see if I could improve that area.
I want to set up 4 Training Cells, one for each of the 4 configurations, and for each of these 4 configurations I want to iterate over all the models and test single fold training for each.

For this, most of the work will of course be focused in ModelBuilding.ipynb and models.py. I want you to name the models BirdCNN_v1, BirdCNN_v2, etc. I want you to try different variations, considering that **we are analyzing grayscale log-mel spectrograms of 5-second bird sound audios, dimensions are (width-time = 313, height-freq = 224), train size expected to be around 2400 samples, some configs may be using Gaussian Noise or SpecAugment augmentations, all configs normalize, most configs standardize**. Within the tests, you can inspire yourself with existing CNN ideas, trying at least 1 of each of the following: {ResNet, VGG, PANN, EfficientNet}, and of course whatever others you might see fit for this case. Try varying layers, Conv Blocks, whatever is worth trying so we can find the best possible architecture for this task.

Once the iterations and are done, follow it up with a basic-metrics plotting cell and a table display cell, like in ModelConfiguring.ipynb. I have laid out templates for these cells too, with commented code that worked on ModelConfiguring (the new code for ModelBuilding will of course have some changes in variable names and such, but should follow the same idea and use the same functions)

Then, since I want 16 models for initial testing, I want one more cell in ModelBuilding.ipynb, plotting a 5x4 of subplots, where each subplot corresponds to one of the 16 models, and displays a column graph with the columns:
- ConfigA Best F1 Score
- ConfigB Best F1 Score
- ConfigC Best F1 Score
- ConfigD Best F1 Score
- Highest F1 Score (max out of the 4 configs)

Also add a Cell like the one we had in ModelConfiguring.ipynb, that takes all information from the top performance of each mode, makes an analysis of the different architectural features (amount of layers, total parameters, conv blocks, residual or not, etc.) and prepares a short indication of how the next potential model could be built for the best performance (with these suggested features).

Lastly, as a detail, add a Cell that saves the models (similar to ModelConfiguring.ipynb last cell, Cell 23), saving to models/reports/ the complete_building_results.json and building_results.csv, with the relevant information.

Remember, work on ModelBuilding.ipynb and models.py, do not modify ModelConfiguring.ipynb. If you see necessary any modifications of util files, you may do them and report them at the end of the implementation. In ModelBuilding, there is most likely no need to modify anything above the "##Training" markdown cell. The Data Pre-Loading Cells are complete as they are.
