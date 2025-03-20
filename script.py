import zipfile
import os
import subprocess

def extract_jar(jar_path, output_dir="extracted_classes"):
    """Extracts the JAR file to a specified directory."""
    try:
        with zipfile.ZipFile(jar_path, 'r') as jar:
            os.makedirs(output_dir, exist_ok=True)
            jar.extractall(output_dir)
            print(f"Extracted JAR to {output_dir}")
            return output_dir
    except FileNotFoundError:
        print(f"File not found: {jar_path}")
        return None
    except zipfile.BadZipFile:
        print(f"Invalid JAR file: {jar_path}")
        return None

def find_controllers_with_reflection(jar_path):
    """Uses Java reflection to find all classes with 'Controller' in their name and print their details."""
    java_code = """
    import java.io.File;
    import java.net.URL;
    import java.net.URLClassLoader;
    import java.util.Enumeration;
    import java.util.jar.JarEntry;
    import java.util.jar.JarFile;

    public class FindControllers {
        public static void main(String[] args) throws Exception {
            String jarPath = args[0];
            JarFile jarFile = new JarFile(jarPath);
            URL[] urls = { new URL("jar:file:" + jarPath + "!/") };
            URLClassLoader cl = URLClassLoader.newInstance(urls);

            System.out.println("Controllers found:");
            Enumeration<JarEntry> entries = jarFile.entries();
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                if (entry.getName().endsWith(".class")) {
                    String className = entry.getName().replace("/", ".").replace(".class", "");
                    try {
                        Class<?> cls = cl.loadClass(className);
                        if (className.contains("Controller")) {
                            System.out.println("Class: " + className);
                            System.out.println("Methods:");
                            for (var method : cls.getDeclaredMethods()) {
                                System.out.println("  " + method);
                            }
                            System.out.println("Fields:");
                            for (var field : cls.getDeclaredFields()) {
                                System.out.println("  " + field);
                            }
                            System.out.println("Annotations:");
                            for (var annotation : cls.getAnnotations()) {
                                System.out.println("  " + annotation);
                            }
                            System.out.println();
                        }
                    } catch (Throwable e) {
                        // Ignore classes that fail to load
                    }
                }
            }
            jarFile.close();
        }
    }
    """
    # Save the Java code to a temporary file
    with open("FindControllers.java", "w") as f:
        f.write(java_code)

    # Compile the Java code
    subprocess.run(["javac", "FindControllers.java"], check=True)

    # Run the Java program
    result = subprocess.run(["java", "FindControllers", jar_path], capture_output=True, text=True)
    print(result.stdout)

def decompile_all_classes(output_dir, decompiler="javap"):
    """Decompiles all class files in the specified directory using javap."""
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".class"):
                class_file_path = os.path.join(root, file)
                print(f"\nDecompiled Java code for {class_file_path}:")
                result = subprocess.run([decompiler, "-c", class_file_path], capture_output=True, text=True)
                print(result.stdout)

def decompile_all_classes_to_java(output_dir="extracted_classes", decompiled_output_dir="decompiled_sources", decompiler_path="cfr.jar"):
    """Decompiles all .class files in the specified directory into .java source code using CFR."""
    try:
        os.makedirs(decompiled_output_dir, exist_ok=True)
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".class"):
                    class_file_path = os.path.join(root, file)
                    print(f"Decompiling {class_file_path}...")
                    result = subprocess.run(
                        ["java", "-jar", decompiler_path, class_file_path, "--outputdir", decompiled_output_dir],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        print(f"Decompiled {class_file_path} to {decompiled_output_dir}")
                    else:
                        print(f"Failed to decompile {class_file_path}: {result.stderr}")
    except Exception as e:
        print(f"Error during decompilation: {e}")

if __name__ == "__main__":
    jar_file_path = "demo-0.0.1-SNAPSHOT.jar"  # Replace with the path to your JAR file
    extracted_dir = extract_jar(jar_file_path)

    if extracted_dir:
        # print("\nFinding controllers using reflection...")
        # find_controllers_with_reflection(jar_file_path)

        # Example: Decompile a specific class (replace with actual class name found)
        output_dir = extracted_dir + "/BOOT-INF/classes" # Replace with the directory containing .class files
        # decompile_all_classes(output_dir)

        print("\nDecompiling .class files to .java source...")
        # Example: Decompile a specific class (replace with actual class name found)
        class_file_path = os.path.join(extracted_dir, "BOOT-INF/classes/com/example/demo/controller/DemoController.class")
        decompiler_jar_path = "cfr.jar"  # Path to the CFR decompiler JAR file
        decompile_all_classes_to_java(output_dir, decompiler_path=decompiler_jar_path)