package org.iqe;

import heronarts.lx.LXComponent;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.structure.LXFixture;
import org.springframework.test.util.ReflectionTestUtils;

import java.lang.reflect.Method;
import java.util.Collection;

/**
 * Ahhh "Utils" classes, "the junk drawers of Java" ™
 * There's a lot of private / final inheritance locking stuff up, attempting to bypass #wcgw?
 */
public class LXUtils {
    public static Object call(Object instance, String method, Object ... args) {
        return ReflectionTestUtils.invokeMethod(instance, method, args);
    }

    public static <T> T field(Class<T> clazz, Object instance, String field) {
        return (T) ReflectionTestUtils.getField(instance, clazz, field);
    }

    public static Object field(Object instance, String field) {
        return ReflectionTestUtils.getField(instance, field);
    }

    public static void addParameter(LXComponent component, String path, LXParameter parameter) {
        call(component, "addParameter", path, parameter);
    }

    public static void removeParameter(LXComponent component, String path) {
        call(component, "removeParameter", path);
    }

    public static void buildOutputs(LXFixture fixture) {
        call(fixture, "buildOutputs");
    }

    public static void regenerateOutputs(LXFixture fixture) {
        call(fixture, "regenerateOutputs");
    }

    public static void addChildRegen(LXFixture fixture, LXFixture child) {
        call(fixture, "addChild", child, true);
    }

    public static Collection<LXParameter> removeAllParameters(LXComponent component) {
        Collection<LXParameter> params = component.getParameters();
        params.forEach(p -> call(component, "removeParameter", p.getPath()));
        return params;
    }
}
