import common.CommandLineValues;
import common.Common;
import model.Word2VecModel;
import org.deeplearning4j.models.word2vec.Word2Vec;
import org.kohsuke.args4j.CmdLineException;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedList;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;

public class App {

    private static CommandLineValues s_CommandLineValues;

    public static void main(String[] args) {
        try {
            s_CommandLineValues = new CommandLineValues(args);
        } catch (CmdLineException e) {
            e.printStackTrace();
            return;
        }

        Common.dimension = s_CommandLineValues.dim > 0 ? s_CommandLineValues.dim : Common.dimension ;

        if (s_CommandLineValues.fit == 1) {
            Word2Vec model = Word2VecModel.initModel(s_CommandLineValues);
            Word2VecModel.saveModel(model, s_CommandLineValues.model_name);
        } else {
            Path path = Paths.get(s_CommandLineValues.source_dir) ;
            if (Files.isDirectory(path)) {
                extractDir();
            } else {
                Word2VecTask task = new Word2VecTask(s_CommandLineValues, path);
                task.call();
            }
        }
    }

    public static void extractDir() {
        ThreadPoolExecutor executor = (ThreadPoolExecutor) Executors.newFixedThreadPool(s_CommandLineValues.NumThreads);
        LinkedList<Word2VecTask> tasks = new LinkedList<>();
        try {
            Files.walk(Paths.get(s_CommandLineValues.source_dir))
                    .filter(Files::isRegularFile)
                    .filter(p -> !p.toString().endsWith(".DS_Store"))
                    .forEach(f -> {
                        Word2VecTask task = new Word2VecTask(s_CommandLineValues, f);
                        tasks.add(task);
                    });
        } catch (IOException e) {
            e.printStackTrace();
            return;
        }
        try {
            executor.invokeAll(tasks);
        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            executor.shutdown();
        }
    }

}
