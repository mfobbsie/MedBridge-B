
import { FORM_CONFIG } from "../config/formConfig";
import { useForm } from "../hooks/useForm";
import type { FormFactoryConfig } from "../types/form";
import type { ReactNode } from "react";



export const FormFactory = ({
  config,
  onSubmit,
  isLoading,
  loadingLabel,
  activeError,
  submitLabel,
  initialData,
}: FormFactoryConfig): ReactNode => {
  const fields = FORM_CONFIG[config] || [];

  const { values, touched, errors, changeHandler, blurHandler } =
    useForm(fields, initialData);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    onSubmit(values as Record<string, string>);
  };

  const errorMessage = 
    typeof activeError === "string"
      ? activeError
      : activeError?.message

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      {errorMessage && (
        <div className="server-error-banner">⚠️ {errorMessage}</div>
      )}

      {fields.map((field) => (
        <div key={field.name} className="form-field">
          <label className="form-label" htmlFor={field.name}>
            {field.label}
          </label>

          {field.type === "select" ? (
            <select
              id={field.name}
              name={field.name}
              value={values[field.name] || ""}
              onChange={changeHandler}
              onBlur={blurHandler}
              disabled={isLoading}
              className="form-input"
            >
              {field.options?.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : field.type === "textarea" ? (
            <textarea
              id={field.name}
              name={field.name}
              value={values[field.name] || ""}
              onChange={changeHandler}
              onBlur={blurHandler}
              disabled={isLoading}
              className="form-input form-textarea"
            />
          ) : (
            <input
              id={field.name}
              type={field.type}
              name={field.name}
              value={values[field.name] || ""}
              onChange={changeHandler}
              onBlur={blurHandler}
              disabled={isLoading}
              className="form-input"
            />
          )}

          {touched[field.name] && errors[field.name] && (
            <span className="form-error">Error: {errors[field.name]}</span>
          )}
        </div>
      ))}

      <button type="submit" className="submit-button" disabled={isLoading}>
      {isLoading ? (loadingLabel || "Submitting...") : submitLabel}
      </button>
    </form>
  );
};

