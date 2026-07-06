interface ErrorComponentProps {
    error?: string;
}


export const ErrorComponent = ({error = "Something went wrong. Please try again."}: ErrorComponentProps) => {
    return (
        <h3 className="error">Error:{error}</h3>
    )
}